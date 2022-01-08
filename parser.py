from os import error
from sly import Parser
from lexer import LangLexer


class LangParser(Parser):
    # AUXILARY FUNCTIONS

    def subtraction(self, value1, value2):
        category1, code1, val1 = value1
        category2, code2, val2 = value2

        if category1 == "num" and category2 == "num":
            return self.generateNumber(val1 - val2)

        if category2 == "num" and val2 >= 0 and val2 <= 10:
            return code1 + val2 * "DEC a\n"

        if category2 == "num" and val2 < 0 and val2 >= -10:
            return code1 + -val2 * "INC a\n"

        return code2 + "SWAP d\n" + code1 + "SUB d\n"

    def optimize_registers(self, tokens):
        ranking = dict()
        for token in tokens:
            if token.type == "PIDENTIFIER" and next(tokens).type != "[":
                if token.value not in ranking:
                    ranking[token.value] = 0
                ranking[token.value] = ranking[token.value] + 1
        sorted_ranking = sorted(
            ranking.items(), key=lambda kv: kv[1], reverse=True)
        if len(sorted_ranking) >= 1:
            self.regs[sorted_ranking[0][0]] = "h"
        if len(sorted_ranking) >= 2:
            self.regs[sorted_ranking[1][0]] = "g"
        if len(sorted_ranking) >= 3:
            self.regs[sorted_ranking[2][0]] = "f"

    # generates a number to register a
    # uses register c as a helper
    def generateNumber(self, num):
        if num >= 0:
            if num <= 20:
                lines = "RESET a\n" + num * "INC a\n"
                return lines
            lines = ""
            while num > 0:
                if num % 2 == 0:
                    num = num // 2
                    lines = "SHIFT c\n" + lines
                else:
                    num = num - 1
                    lines = "INC a\n" + lines
            lines = "RESET a\n" + "RESET c\n" + "INC c\n" + lines
            return lines

        num = -num
        if num <= 20:
            lines = "RESET a\n" + num * "DEC a\n"
            return lines
        lines = ""
        while num > 0:
            if num % 2 == 0:
                num = num // 2
                lines = "SHIFT c\n" + lines
            else:
                num = num - 1
                lines = "DEC a\n" + lines
        lines = "RESET a\n" + "RESET c\n" + "INC c\n" + lines
        return lines

    # ERROR CHECKERS

    tokens = LangLexer.tokens

    precedence = (
        ('nonassoc', 'EQ', 'NEQ', 'LE', 'GE', 'LEQ', 'GEQ'),
        ('left', 'PLUS', 'MINUS'),
        ('left', 'TIMES', 'DIV', 'MOD'),
    )

    def __init__(self):
        self.var = {}
        self.arr = {}
        self.iter = {}
        self.regs = {}
        self.inits = set()
        self.memtop = 0

    @_('VAR declarations BEGIN commands END')
    def program(self, p):
        return p[3] + "HALT"

    @_('BEGIN commands END')
    def program(self, p):
        return p[1] + "HALT"

    @_('declarations "," PIDENTIFIER')
    def declarations(self, p):
        id = p[2]

        if id in self.var or id in self.arr:
            msg = f"Błąd w linii {p.lineno}: druga deklaracja {id}"
            raise Exception(msg)

        if id in self.regs:
            self.var[id] = ("reg", self.regs[id])
        else:
            self.var[id] = ("mem", self.memtop)
            self.memtop += 1

    @_('declarations "," PIDENTIFIER "[" NUM ":" NUM "]"')
    def declarations(self, p):
        id = p[2]
        first = p[4]
        last = p[6]

        if id in self.var or id in self.arr:
            msg = f"Błąd w linii {p.lineno}: druga deklaracja {id}"
            raise Exception(msg)

        if last < first:
            msg = f"Błąd w linii {p.lineno}: niewłaściwy zakres tablicy {id}"
            raise Exception(msg)

        self.arr[id] = (self.memtop, first, last)
        self.memtop += last - first + 1

    @_('PIDENTIFIER')
    def declarations(self, p):
        id = p[0]

        if id in self.regs:
            self.var[id] = ("reg", self.regs[id])
        else:
            self.var[id] = ("mem", self.memtop)
            self.memtop += 1

    @_('PIDENTIFIER "[" NUM ":" NUM "]"')
    def declarations(self, p):
        id = p[0]
        first = p[2]
        last = p[4]

        if last < first:
            msg = f"Błąd w linii {p.lineno}: niewłaściwy zakres tablicy {id}"
            raise Exception(msg)

        self.arr[id] = (self.memtop, first, last)
        self.memtop += last - first + 1

    @_('commands command')
    def commands(self, p):
        return p[0] + p[1]

    @_('command')
    def commands(self, p):
        return p[0]

    @_('identifier ASSIGN expression ";"')
    def command(self, p):
        category, id, code1, _ = p[0]
        code2 = p[2]

        if category == "var":
            self.inits.add(id)

        if category == "var_reg":
            return code2 + f"SWAP {self.regs[id]}\n"
        return code2 + "SWAP d\n" + code1 + "SWAP d\n" + "STORE d\n"

    @_('IF condition THEN commands ELSE commands ENDIF')
    def command(self, p):
        cond_category, cond_code = p[1]
        inner_code = p[3]
        inner_len = inner_code.count('\n')
        else_code = p[5]
        else_len = else_code.count('\n')

        if cond_category == "eq":
            return cond_code + f"JZERO {else_len + 2}\n" + else_code + f"JUMP {inner_len + 1}\n" + inner_code
        if cond_category == "neq":
            return cond_code + f"JZERO {inner_len + 2}\n" + inner_code + f"JUMP {else_len + 1}\n" + else_code
        if cond_category == "le":
            return cond_code + f"JNEG {else_len + 2}\n" + else_code + f"JUMP {inner_len + 1}\n" + inner_code
        if cond_category == "geq":
            return cond_code + f"JNEG {inner_len + 2}\n" + inner_code + f"JUMP {else_len + 1}\n" + else_code
        if cond_category == "ge":
            return cond_code + f"JPOS {else_len + 2}\n" + else_code + f"JUMP {inner_len + 1}\n" + inner_code
        if cond_category == "leq":
            return cond_code + f"JPOS {inner_len + 2}\n" + inner_code + f"JUMP {else_len + 1}\n" + else_code

    @_('IF condition THEN commands ENDIF')
    def command(self, p):
        cond_category, cond_code = p[1]
        inner_code = p[3]
        inner_len = inner_code.count('\n')

        if cond_category == "eq":
            return cond_code + "JZERO 2\n" + f"JUMP {inner_len + 1}\n" + inner_code
        if cond_category == "neq":
            return cond_code + f"JZERO {inner_len + 1}\n" + inner_code
        if cond_category == "le":
            return cond_code + "JNEG 2\n" + f"JUMP {inner_len + 1}\n" + inner_code
        if cond_category == "geq":
            return cond_code + f"JNEG {inner_len + 1}\n" + inner_code
        if cond_category == "ge":
            return cond_code + "JPOS 2\n" + f"JUMP {inner_len + 1}\n" + inner_code
        if cond_category == "leq":
            return cond_code + f"JPOS {inner_len + 1}\n" + inner_code

    @_('WHILE condition DO commands ENDWHILE')
    def command(self, p):
        cond_category, cond_code = p[1]
        cond_len = cond_code.count('\n')
        inner_code = p[3]
        inner_len = inner_code.count('\n')

        if cond_category == "eq":
            return cond_code + "JZERO 2\n" + f"JUMP {inner_len + 2}\n" + inner_code + f"JUMP {-2 - cond_len -inner_len}\n"
        if cond_category == "neq":
            return cond_code + f"JZERO {inner_len + 2}\n" + inner_code + f"JUMP {-1 - cond_len -inner_len}\n"
        if cond_category == "le":
            return cond_code + "JNEG 2\n" + f"JUMP {inner_len + 2}\n" + inner_code + f"JUMP {-2 - cond_len -inner_len}\n"
        if cond_category == "geq":
            return cond_code + f"JNEG {inner_len + 2}\n" + inner_code + f"JUMP {-1 - cond_len -inner_len}\n"
        if cond_category == "ge":
            return cond_code + "JPOS 2\n" + f"JUMP {inner_len + 2}\n" + inner_code + f"JUMP {-2 - cond_len -inner_len}\n"
        if cond_category == "leq":
            return cond_code + f"JPOS {inner_len + 2}\n" + inner_code + f"JUMP {-1 - cond_len -inner_len}\n"

    @_('REPEAT commands UNTIL condition ";"')
    def command(self, p):
        inner_code = p[1]
        cond_category, cond_code = p[3]
        cond_len = cond_code.count('\n')
        inner_len = inner_code.count('\n')

        if cond_category == "eq":
            return inner_code + cond_code + "JZERO 2\n" + f"JUMP {-inner_len -cond_len - 1}\n"
        if cond_category == "neq":
            return inner_code + cond_code + f"JZERO  {-inner_len -cond_len}\n"
        if cond_category == "le":
            return inner_code + cond_code + "JNEG 2\n" + f"JUMP {-inner_len -cond_len - 1}\n"
        if cond_category == "geq":
            return inner_code + cond_code + f"JNEG  {-inner_len -cond_len}\n"
        if cond_category == "ge":
            return inner_code + cond_code + "JPOS 2\n" + f"JUMP {-inner_len -cond_len - 1}\n"
        if cond_category == "leq":
            return inner_code + cond_code + f"JPOS  {-inner_len -cond_len}\n"

    @_('FOR PIDENTIFIER FROM value TO value DO commands ENDFOR')
    def command(self, p):
        id = p[1]
        from_code = p[3] 
        to_code = p[5]
        inner_code = p[7]
        from_register = False

        # TODO: kod bez rejestrów
        if id not in self.regs:
            self.iter[id] = self.memtop
            self.memtop += 1

            return self.generateNumber[self.iter[id]] +\
            "SWAP b\n" +\
            from_code +\
            "DEC a" +\
            "STORE b\n" +\
            "JUMP 1\n" +\
            self.generateNumber[self.iter[id]] +\
            "SWAP b\n" +\
            "LOAD b\n" +\
            "INC a\n" +\
            "STORE b\n" +\
            to_code +\
            "SWAP b\n" +\
            self.generateNumber[self.iter[id]] +\
            "LOAD a\n" +\
            "SUB b\n" +\
            "JNEG 1\n" +\
            inner_code +\
            "JUMP 1\n"
        else:
            self.iter[id] = ("reg", self.regs[id])
            reg = self.regs[id]
            inner_len = inner_code.count('\n')
            to_code_len = to_code.count('\n')

            return from_code +\
            "DEC a\n" +\
            f"SWAP {reg}\n" +\
            to_code +\
            f"INC {reg}\n" +\
            f"SUB {reg}\n" +\
            f"JNEG {inner_code + 1}\n" +\
            inner_code +\
            f"JUMP {-inner_len -to_code_len -3}\n"      

    @_('FOR PIDENTIFIER FROM value DOWNTO value DO commands ENDFOR')
    def command(self, p):
        id = p[1]
        from_code = p[3] 
        to_code = p[5]
        inner_code = p[7]
        from_register = False
        print(self.iter)

        # TODO: kod bez rejestrów
        if id not in self.regs:
            self.iter[id] = self.memtop
            self.memtop += 1

            return self.generateNumber[self.iter[id]] +\
            "SWAP b\n" +\
            from_code +\
            "DEC a" +\
            "STORE b\n" +\
            "JUMP 1\n" +\
            self.generateNumber[self.iter[id]] +\
            "SWAP b\n" +\
            "LOAD b\n" +\
            "INC a\n" +\
            "STORE b\n" +\
            to_code +\
            "SWAP b\n" +\
            self.generateNumber[self.iter[id]] +\
            "LOAD a\n" +\
            "SUB b\n" +\
            "JNEG 1\n" +\
            inner_code +\
            "JUMP 1\n"
        else:
            self.iter[id] = ("reg", self.regs[id])
            reg = self.regs[id]
            inner_len = inner_code.count('\n')
            to_code_len = to_code.count('\n')

            return from_code +\
            "INC a\n" +\
            f"SWAP {reg}\n" +\
            to_code +\
            f"DEC {reg}\n" +\
            f"SUB {reg}\n" +\
            f"JPOS {inner_code + 1}\n" +\
            inner_code +\
            f"JUMP {-inner_len -to_code_len -3}\n" 

    @_('READ identifier ";"')
    def command(self, p):
        category, id, code, _ = p[1]
        self.inits.add(id)
        if category == "var":
            return code + "SWAP b\n" + "GET\n" + "STORE b\n"
        if category == "var_reg":
            return "GET\n" + f"SWAP {self.regs[id]}"

    @_('WRITE value ";"')
    def command(self, p):
        return p[1][1] + "PUT\n"

    # loads value to register a
    @_('value')
    def expression(self, p):
        return p[0][1]

    @_('value PLUS value')
    def expression(self, p):
        category1, code1, val1 = p[0]
        category2, code2, val2 = p[2]

        if category1 == "num" and category2 == "num":
            return self.generateNumber(val1 + val2)

        if category1 == "num" and val1 >= 0 and val1 <= 10:
            return code2 + val1 * "INC a\n"

        if category1 == "num" and val1 < 0 and val1 >= -10:
            return code2 + -val1 * "DEC a\n"

        if category2 == "num" and val2 >= 0 and val2 <= 10:
            return code1 + val2 * "INC a\n"

        if category2 == "num" and val2 < 0 and val2 >= -10:
            return code1 + -val2 * "DEC a\n"

        return code2 + "SWAP d\n" + code1 + "ADD d\n"

    @_('value MINUS value')
    def expression(self, p):
        return self.subtraction(p[0], p[2])

    @_('value TIMES value')
    def expression(self, p):
        category1, code1, val1 = p[0]
        category2, code2, val2 = p[2]

        if category1 == "num" and category2 == "num":
            return self.generateNumber(val1 * val2)

        lines = ""
        if category1 == "num":
            if val1 == -1:
                return code2 + "SWAP d\n" + "RESET a\n" + "SUB d\n"

            if val1 == 0:
                return "RESET a\n"

            if val1 == 1:
                return code2

            oper = "ADD b\n"
            if val1 < 0:
                val1 = -val1
                oper = "SUB b\n"

            while val1 > 0:
                if val1 % 2 == 0:
                    lines = "SHIFT d\n" + lines
                    val1 = val1 // 2
                else:
                    lines = oper + lines
                    val1 = val1 - 1
            return code2 + 'SWAP b\n' + "RESET a\n" + "RESET d\n" + "INC d\n" + lines

        if category2 == "num":
            if val2 == -1:
                return code1 + "SWAP d\n" + "RESET a\n" + "SUB d\n"

            if val2 == 0:
                return "RESET a\n"

            if val2 == 1:
                return code1

            oper = "ADD b\n"
            if val2 < 0:
                val2 = -val2
                oper = "SUB b\n"

            while val2 > 0:
                if val2 % 2 == 0:
                    lines = "SHIFT d\n" + lines
                    val2 = val2 // 2
                else:
                    lines = oper + lines
                    val2 = val2 - 1
            return code1 + 'SWAP b\n' + "RESET a\n" + "RESET d\n" + "INC d\n" + lines

        lines = code2 +\
            "SWAP d\n" +\
            code1 +\
            "SWAP c\n" +\
            "RESET e\n" +\
            "INC e\n" +\
            "RESET f\n" +\
            "DEC f\n" +\
            "RESET b\n" +\
            "SWAP d\n" +\
            "JPOS 9\n" +\
            "JZERO 25\n" +\
            "SWAP d\n" +\
            "RESET a\n" +\
            "SUB c\n" +\
            "SWAP c\n" +\
            "RESET a\n" +\
            "SUB d\n" +\
            "JZERO 17\n" +\
            "SWAP d\n" +\
            "RESET a\n" +\
            "ADD d\n" +\
            "SHIFT f\n" +\
            "SHIFT e\n" +\
            "SUB d\n" +\
            "JZERO 4\n" +\
            "SWAP b\n" +\
            "ADD c\n" +\
            "SWAP b\n" +\
            "SWAP c\n" +\
            "SHIFT e\n" +\
            "SWAP c\n" +\
            "SWAP d\n" +\
            "SHIFT f\n" +\
            "JUMP -16\n" +\
            "SWAP b\n"
        return lines

    @_('value DIV value')
    def expression(self, p):
        category1, code1, val1 = p[0]
        category2, code2, val2 = p[2]

        if category2 == "num":
            if val2 == 0:
                return "RESET a\n"

            if val2 == 1:
                return code1

            if val2 == -1:
                return code1 + "SWAP b\n" + "RESET a\n" + "SUB b\n"

        if category1 == "num":
            if val1 == 0:
                return "RESET a\n"

        # loading values, dividend to d, divisor to e
        lines = code1 + "SWAP d\n" + code2 + "SWAP e\n"

        # calculating msb to register b
        pos_case = "RESET a\n" +\
            "RESET b\n" +\
            "RESET c\n" +\
            "DEC c\n" +\
            "ADD d\n" +\
            "JPOS 2\n" +\
            "JUMP 4\n" +\
            "SHIFT c\n" +\
            "INC b\n" +\
            "JUMP -4\n"
        # setting divisor to divisor << (mst+1), and c (quotient) to 0
        pos_case += "SWAP e\n" +\
            "INC b\n" +\
            "SHIFT b\n" +\
            "DEC b\n" +\
            "SWAP e\n" +\
            "SWAP b\n" +\
            "RESET c\n"
        # while loop
        pos_case += "JNEG 23\n" +\
            "SWAP b\n" +\
            "SWAP e\n" +\
            "RESET e\n" +\
            "DEC e\n" +\
            "SHIFT e\n" +\
            "SWAP e\n" +\
            "RESET a\n" +\
            "ADD d\n" +\
            "SUB e\n" +\
            "JNEG 10\n" +\
            "RESET a\n" +\
            "SWAP d\n" +\
            "SUB e\n" +\
            "SWAP d\n" +\
            "RESET a\n" +\
            "INC a\n" +\
            "SHIFT b\n" +\
            "ADD c\n" +\
            "SWAP c\n" +\
            "DEC b\n" +\
            "SWAP b\n" +\
            "JUMP -22\n" +\
            "SWAP c\n"

        # negate result, and have fun with floor
        neg_case = pos_case +\
            "SWAP c\n" +\
            "SWAP d\n" +\
            "JZERO 2\n" +\
            "INC c\n" +\
            "RESET a\n" +\
            "SUB c\n"

        pos_len = pos_case.count('\n')
        neg_len = neg_case.count('\n')

        # divisor in register a in the beginning
        non_zero_divisor = f"JPOS {12 + pos_len}\n" +\
            "SWAP e\n" +\
            "RESET a\n" +\
            "SUB e\n" +\
            "SWAP e\n" +\
            "SWAP d\n" +\
            f"JPOS {12 + pos_len}\n" +\
            "SWAP d\n" +\
            "RESET a\n" +\
            "SUB d\n" +\
            "SWAP d\n" +\
            pos_case +\
            f"JUMP {10 + neg_len}\n" +\
            "SWAP e\n" +\
            "SWAP d\n" +\
            f"JPOS {-4 -pos_len}\n" +\
            "SWAP d\n" +\
            "RESET a\n" +\
            "SUB d\n" +\
            "SWAP d\n" +\
            neg_case +\
            "JUMP 2\n"

        non_zero_len = non_zero_divisor.count('\n')

        lines += "SWAP e\n" +\
            f"JZERO {non_zero_len + 1}\n" +\
            non_zero_divisor +\
            "RESET a\n"

        return lines

    @_('value MOD value')
    def expression(self, p):
        category1, code1, val1 = p[0]
        category2, code2, val2 = p[2]

        if category2 == "num":
            if val2 == 0:
                return "RESET a\n"

            if val2 == 1:
                return "RESET a\n"

            if val2 == -1:
                return "RESET a\n"

        if category1 == "num":
            if val1 == 0:
                return "RESET a\n"

        # loading values, dividend to d, divisor to e
        lines = code1 + "SWAP d\n" + code2 + "SWAP e\n"

        # calculating msb to register b
        pp_case = "RESET a\n" +\
            "RESET b\n" +\
            "RESET c\n" +\
            "DEC c\n" +\
            "ADD d\n" +\
            "JPOS 2\n" +\
            "JUMP 4\n" +\
            "SHIFT c\n" +\
            "INC b\n" +\
            "JUMP -4\n"
        # setting divisor to divisor << (mst+1), and c (quotient) to 0
        pp_case += "SWAP e\n" +\
            "INC b\n" +\
            "SHIFT b\n" +\
            "DEC b\n" +\
            "SWAP e\n" +\
            "SWAP b\n" +\
            "RESET c\n"
        # while loop
        pp_case += "JNEG 23\n" +\
            "SWAP b\n" +\
            "SWAP e\n" +\
            "RESET e\n" +\
            "DEC e\n" +\
            "SHIFT e\n" +\
            "SWAP e\n" +\
            "RESET a\n" +\
            "ADD d\n" +\
            "SUB e\n" +\
            "JNEG 10\n" +\
            "RESET a\n" +\
            "SWAP d\n" +\
            "SUB e\n" +\
            "SWAP d\n" +\
            "RESET a\n" +\
            "INC a\n" +\
            "SHIFT b\n" +\
            "ADD c\n" +\
            "SWAP c\n" +\
            "DEC b\n" +\
            "SWAP b\n" +\
            "JUMP -22\n" +\
            "SWAP d\n"

        pn_case = pp_case +\
            "JZERO 2\n" +\
            "SUB e\n"

        nn_case = pp_case +\
            "SWAP d\n" +\
            "RESET a\n" +\
            "SUB d\n"

        np_case = pp_case +\
            "SWAP d\n" +\
            "RESET a\n" +\
            "SUB d\n" +\
            "JZERO 2\n" +\
            "ADD e\n"

        pp_len = pp_case.count('\n')
        pn_len = pn_case.count('\n')
        np_len = np_case.count('\n')
        nn_len = nn_case.count('\n')

        # divisor in register a in the beginning
        non_zero_divisor = f"JPOS {14 + nn_len + pn_len}\n" +\
            "SWAP e\n" +\
            "RESET a\n" +\
            "SUB e\n" +\
            "SWAP e\n" +\
            "SWAP d\n" +\
            f"JPOS {6 + nn_len}\n" +\
            "SWAP d\n" +\
            "RESET a\n" +\
            "SUB d\n" +\
            "SWAP d\n" +\
            nn_case +\
            f"JUMP {12 + pn_len + np_len + pp_len}\n" +\
            "SWAP d\n" +\
            pn_case +\
            f"JUMP {10 + np_len + pp_len}\n" +\
            "SWAP e\n" +\
            "SWAP d\n" +\
            f"JPOS {6 + np_len}\n" +\
            "SWAP d\n" +\
            "RESET a\n" +\
            "SUB d\n" +\
            "SWAP d\n" +\
            np_case +\
            f"JUMP {4 + pp_len}\n" +\
            "SWAP d\n" +\
            pp_case +\
            "JUMP 2\n"

        non_zero_len = non_zero_divisor.count('\n')

        lines += "SWAP e\n" +\
            f"JZERO {non_zero_len + 1}\n" +\
            non_zero_divisor +\
            "RESET a\n"

        return lines

    @_('value EQ value')
    def condition(self, p):
        return ("eq", self.subtraction(p[0], p[2]))

    @_('value NEQ value')
    def condition(self, p):
        return ("neq", self.subtraction(p[0], p[2]))

    @_('value LE value')
    def condition(self, p):
        return ("le", self.subtraction(p[0], p[2]))

    @_('value GE value')
    def condition(self, p):
        return ("ge", self.subtraction(p[0], p[2]))

    @_('value LEQ value')
    def condition(self, p):
        return ("leq", self.subtraction(p[0], p[2]))

    @_('value GEQ value')
    def condition(self, p):
        return ("geq", self.subtraction(p[0], p[2]))

    # loads value to register a
    @_('NUM')
    def value(self, p):
        return ("num", self.generateNumber(p[0]), p[0])

    # loads value to register a
    @_('identifier')
    def value(self, p):
        category, id, code, lineno = p[0]

        if category == "var" and id not in self.inits:
            msg = f"Błąd w linii {lineno}: użycie niezainicjowanej zmiennej {id}"
            raise Exception(msg)

        if category == "var_reg":
            return (category, f"RESET a\n ADD {self.regs[id]}\n", None)

        return (category, code + "LOAD a\n", None)

    # loads address to register a
    # returns loaded address and generated code
    @_('PIDENTIFIER')
    def identifier(self, p):
        id = p[0]

        if id in self.arr:
            msg = f"Błąd w linii {p.lineno}: niewłaściwe użycie zmiennej tablicowej {id}"
            raise Exception(msg)

        if id in self.iter:
            return ("iter", id, self.generateNumber(self.iter[id]), p.lineno)

        if id not in self.var:
            msg = f"Błąd w linii {p.lineno}: niezadeklarowana zmienna {id}"
            raise Exception(msg)

        category, address = self.var[id]
        if category == "mem":
            return ("var", id, self.generateNumber(address), p.lineno)
        else:
            return ("var_reg", id, None, p.lineno)

    @_('PIDENTIFIER "[" NUM "]"')
    def identifier(self, p):
        tab = p[0]
        id = p[2]

        if tab in self.var or tab in self.iter:
            msg = f"Błąd w linii {p.lineno}: niewłaściwe użycie zmiennej {tab}"
            raise Exception(msg)

        if tab not in self.arr:
            msg = f"Błąd w linii {p.lineno}: niezadeklarowana zmienna tablicowa {tab}"
            raise Exception(msg)

        memtop, first, last = self.arr[tab]

        if id < first or id > last:
            msg = f"Błąd w linii {p.lineno}: indeks {id} poza zakresem tablicy {tab}"
            raise Exception(msg)

        return ("arr", tab, self.generateNumber(memtop + id - first), p.lineno)

    @_('PIDENTIFIER "[" PIDENTIFIER "]"')
    def identifier(self, p):
        tab = p[0]
        id = p[2]

        if tab in self.var or tab in self.iter:
            msg = f"Błąd w linii {p.lineno}: niewłaściwe użycie zmiennej {tab}"
            raise Exception(msg)

        if tab not in self.arr:
            msg = f"Błąd w linii {p.lineno}: niezadeklarowana zmienna tablicowa {tab}"
            raise Exception(msg)

        memtop, first, _ = self.arr[tab]

        if id in self.arr:
            msg = f"Błąd w linii {p.lineno}: niewłaściwe użycie zmiennej {id}"
            raise Exception(msg)

        if id not in self.inits and id not in self.iter:
            msg = f"Błąd w linii {p.lineno}: użycie niezainicjowanej zmiennej {id}"
            raise Exception(msg)

        lines = ""
        category, address = self.var[id]
        if category == "mem":
            lines += self.generateNumber(address)
            lines += "LOAD a\n SWAP b\n"
        else:
            lines += f"RESET a\n ADD {self.var[id][1]}\n SWAP b\n"
        lines += self.generateNumber(memtop - first)
        lines += "ADD b\n"

        return ("arr", tab, lines, p.lineno)

    def error(self, p):
        msg = f"Błąd w linii {p.lineno}: nierozpoznany napis {p.value}"
        raise Exception(msg)
