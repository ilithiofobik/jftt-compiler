from os import error
from sly import Parser
from lexer import LangLexer


class LangParser(Parser):
    # CHECKING DECLARATION AND INITIALIZATION

    def checkVar(self, id, lineno):
        if id in self.arr:
            msg = f"Błąd w linii {lineno}: niewłaściwe użycie zmiennej tablicowej {id}"
            raise Exception(msg)

        if id not in self.var and id not in self.iter:
            msg = f"Błąd w linii {lineno}: niezadeklarowana zmienna {id}"
            raise Exception(msg)

    def checkInit(self, id, lineno):
        if id not in self.inits and id not in self.iter:
            msg = f"Błąd w linii {lineno}: użycie niezainicjowanej zmiennej {id}"
            raise Exception(msg)

    def checkArr(self, tab, lineno):
        if tab in self.var or tab in self.iter:
            msg = f"Błąd w linii {lineno}: niewłaściwe użycie zmiennej {tab}"
            raise Exception(msg)

        if tab not in self.arr:
            msg = f"Błąd w linii {lineno}: niezadeklarowana zmienna tablicowa {tab}"
            raise Exception(msg)

    # ARITHMETICS

    def addition(self, value1, value2):
        category1, code1, val1 = value1
        category2, code2, val2 = value2

        if category1 == "num" and category2 == "num":
            return self.generateNumber(val1 + val2)

        if category1 == "num" and val1 >= 0 and val1 <= 7:
            return code2 + val1 * "INC a\n"

        if category1 == "num" and val1 < 0 and val1 >= -7:
            return code2 + -val1 * "DEC a\n"

        if category2 == "num" and val2 >= 0 and val2 <= 7:
            return code1 + val2 * "INC a\n"

        if category2 == "num" and val2 < 0 and val2 >= -7:
            return code1 + -val2 * "DEC a\n"

        if val1 == val2:
            return code1 + "RESET d\n" + "INC d\n" + "SHIFT d\n"

        return code2 + "SWAP d\n" + code1 + "ADD d\n"

    def subtraction(self, value1, value2):
        category1, code1, val1 = value1
        category2, code2, val2 = value2

        if category1 == "num" and category2 == "num":
            return self.generateNumber(val1 - val2)

        if category2 == "num" and val2 >= 0 and val2 <= 7:
            return code1 + val2 * "DEC a\n"

        if category2 == "num" and val2 < 0 and val2 >= -7:
            return code1 + -val2 * "INC a\n"

        if val1 == val2:
            return "RESET a\n"

        return code2 + "SWAP d\n" + code1 + "SUB d\n"

    def multiplication(self, value1, value2):
        category1, code1, val1 = value1
        category2, code2, val2 = value2

        if category1 == "num" and category2 == "num":
            return self.generateNumber(val1 * val2)

        lines = ""
        if category1 == "num" or category2 == "num":
            if category2 == "num":
                category1, code1, val1 = value2
                category2, code2, val2 = value1

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

        lines = code2 +\
            "SWAP d\n" +\
            code1 +\
            "SWAP c\n" +\
            "RESET e\n" +\
            "INC e\n" +\
            "RESET b\n" +\
            "SWAP d\n" +\
            "JPOS 9\n" +\
            "JZERO 33\n" +\
            "SWAP d\n" +\
            "RESET a\n" +\
            "SUB c\n" +\
            "SWAP c\n" +\
            "RESET a\n" +\
            "SUB d\n" +\
            "JZERO 25\n" +\
            "SWAP d\n" +\
            "RESET a\n" +\
            "ADD d\n" +\
            "RESET e\n" +\
            "DEC e\n" +\
            "SHIFT e\n" +\
            "RESET e\n" +\
            "INC e\n" +\
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
            "RESET e\n" +\
            "DEC e\n" +\
            "SHIFT e\n" +\
            "RESET e\n" +\
            "INC e\n" +\
            "JUMP -24\n" +\
            "SWAP b\n"
        return lines

    def division(self, value1, value2):
        category1, code1, val1 = value1
        category2, code2, val2 = value2

        if category1 == "num" and category2 == "num":
            if val2 == 0:
                return "RESET a\n"
            else:
                return self.generateNumber(val1 // val2)

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

        if val1 == val2:
            return code1 +\
                "JZERO 3\n" +\
                "RESET a\n" +\
                "INC a\n"

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

    def modulo(self, value1, value2):
        category1, code1, val1 = value1
        category2, code2, val2 = value2

        if category1 == "num" and category2 == "num":
            if val2 == 0:
                return "RESET a\n"
            else:
                return self.generateNumber(val1 % val2)

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

        if val1 == val2:
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
    # OPTIMIZATION FUNCTIONS

    def optimize_registers(self, tokens):
        ranking = dict()
        e_reserved = False
        for token in tokens:
            if token.type in ["TIMES", "DIV", "MOD"]:
                e_reserved = True
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

    # GENERATING NUMBERS

    def generateNumber(self, num):
        little_magic_number = 7
        big_magic_number = 256
        inc_dec = "INC a\n"

        if num < 0:
            num = -num
            inc_dec = "DEC a\n"

        if num <= little_magic_number:
            lines = "RESET a\n" + num * inc_dec
            return lines

        # 2^n in log(log(n)) time
        if num >= big_magic_number and num & (num - 1) == 0:
            log_num = 0

            while num >= 2:
                log_num += 1
                num = num // 2

            lines = ""

            while log_num > 0:
                if log_num % 2 == 0:
                    log_num = log_num // 2
                    lines = "SHIFT c\n" + lines
                else:
                    log_num = log_num - 1
                    lines = "INC a\n" + lines

            return "RESET a\n" + "RESET c\n" + "INC c\n" + lines + "SWAP c\n" + "RESET a\n" + inc_dec + "SHIFT c\n"

        lines = ""
        while num > 0:
            if num % 2 == 0:
                num = num // 2
                lines = "SHIFT c\n" + lines
            else:
                num = num - 1
                lines = inc_dec + lines
        return "RESET a\n" + "RESET c\n" + "INC c\n" + lines

    # PROPER PARSER

    tokens = LangLexer.tokens

    precedence = (
        ('nonassoc', 'EQ', 'NEQ', 'LE', 'GE', 'LEQ', 'GEQ'),
        ('nonassoc', 'PLUS', 'MINUS'),
        ('nonassoc', 'TIMES', 'DIV', 'MOD'),
    )

    def __init__(self):
        self.var = {}
        self.arr = {}
        self.iter = {}
        self.regs = {}
        self.inits = set()
        self.memtop = 0

    # PROGRAM

    @_('VAR declarations BEGIN commands END')
    def program(self, p):
        return p[3] + "HALT"

    @_('BEGIN commands END')
    def program(self, p):
        return p[1] + "HALT"

    # DECLARATIONS

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

    # COMMANDS

    @_('commands command')
    def commands(self, p):
        if type(p[1]) == type(()):
            self.iter.pop(p[1][1])
            return p[0] + p[1][0]
        return p[0] + p[1]

    @_('command')
    def commands(self, p):
        if type(p[0]) == type(()):
            self.iter.pop(p[0][1])
            return p[0][0]
        return p[0]

    @_('identifier ASSIGN expression ";"')
    def command(self, p):
        category, id, code1, lineno = p[0]
        first_val, oper, second_val = p[2]

        if oper == "PLUS":
            code2 = self.addition(first_val, second_val)
        if oper == "MINUS":
            code2 = self.subtraction(first_val, second_val)
        if oper == "TIMES":
            code2 = self.multiplication(first_val, second_val)
        if oper == "DIV":
            code2 = self.division(first_val, second_val)
        if oper == "MOD":
            code2 = self.modulo(first_val, second_val)
        if oper is None:
            code2 = first_val[1]

        if id in self.iter:
            msg = f"Błąd w linii {lineno}: zabroniona modyfikacja iteratora {id}"
            raise Exception(msg)

        if category == "var":
            self.inits.add(id)

        if category == "var_reg":
            self.inits.add(id)
            return code2 + f"SWAP {self.regs[id]}\n"

        return code2 + "SWAP d\n" + code1 + "SWAP d\n" + "STORE d\n"

    @_('IF condition THEN commands ELSE commands ENDIF')
    def command(self, p):
        cond_category, cond_code = p[1]
        inner_code = p[3]
        inner_len = inner_code.count('\n')
        else_code = p[5]
        else_len = else_code.count('\n')

        if cond_category == "EQ":
            return cond_code + f"JZERO {else_len + 2}\n" + else_code + f"JUMP {inner_len + 1}\n" + inner_code
        if cond_category == "NEQ":
            return cond_code + f"JZERO {inner_len + 2}\n" + inner_code + f"JUMP {else_len + 1}\n" + else_code
        if cond_category == "LE":
            return cond_code + f"JNEG {else_len + 2}\n" + else_code + f"JUMP {inner_len + 1}\n" + inner_code
        if cond_category == "GEQ":
            return cond_code + f"JNEG {inner_len + 2}\n" + inner_code + f"JUMP {else_len + 1}\n" + else_code
        if cond_category == "GE":
            return cond_code + f"JPOS {else_len + 2}\n" + else_code + f"JUMP {inner_len + 1}\n" + inner_code
        if cond_category == "LEQ":
            return cond_code + f"JPOS {inner_len + 2}\n" + inner_code + f"JUMP {else_len + 1}\n" + else_code

    @_('IF condition THEN commands ENDIF')
    def command(self, p):
        cond_category, cond_code = p[1]
        inner_code = p[3]
        inner_len = inner_code.count('\n')

        if cond_category == "EQ":
            return cond_code + "JZERO 2\n" + f"JUMP {inner_len + 1}\n" + inner_code
        if cond_category == "NEQ":
            return cond_code + f"JZERO {inner_len + 1}\n" + inner_code
        if cond_category == "LE":
            return cond_code + "JNEG 2\n" + f"JUMP {inner_len + 1}\n" + inner_code
        if cond_category == "GEQ":
            return cond_code + f"JNEG {inner_len + 1}\n" + inner_code
        if cond_category == "GE":
            return cond_code + "JPOS 2\n" + f"JUMP {inner_len + 1}\n" + inner_code
        if cond_category == "LEQ":
            return cond_code + f"JPOS {inner_len + 1}\n" + inner_code

    @_('WHILE condition DO commands ENDWHILE')
    def command(self, p):
        cond_category, cond_code = p[1]
        cond_len = cond_code.count('\n')
        inner_code = p[3]
        inner_len = inner_code.count('\n')

        if cond_category == "EQ":
            return cond_code + "JZERO 2\n" + f"JUMP {inner_len + 2}\n" + inner_code + f"JUMP {-2 - cond_len -inner_len}\n"
        if cond_category == "NEQ":
            return cond_code + f"JZERO {inner_len + 2}\n" + inner_code + f"JUMP {-1 - cond_len -inner_len}\n"
        if cond_category == "LE":
            return cond_code + "JNEG 2\n" + f"JUMP {inner_len + 2}\n" + inner_code + f"JUMP {-2 - cond_len -inner_len}\n"
        if cond_category == "GEQ":
            return cond_code + f"JNEG {inner_len + 2}\n" + inner_code + f"JUMP {-1 - cond_len -inner_len}\n"
        if cond_category == "GE":
            return cond_code + "JPOS 2\n" + f"JUMP {inner_len + 2}\n" + inner_code + f"JUMP {-2 - cond_len -inner_len}\n"
        if cond_category == "LEQ":
            return cond_code + f"JPOS {inner_len + 2}\n" + inner_code + f"JUMP {-1 - cond_len -inner_len}\n"

    @_('REPEAT commands UNTIL condition ";"')
    def command(self, p):
        inner_code = p[1]
        cond_category, cond_code = p[3]
        cond_len = cond_code.count('\n')
        inner_len = inner_code.count('\n')

        if cond_category == "EQ":
            return inner_code + cond_code + "JZERO 2\n" + f"JUMP {-inner_len -cond_len - 1}\n"
        if cond_category == "NEQ":
            return inner_code + cond_code + f"JZERO  {-inner_len -cond_len}\n"
        if cond_category == "LE":
            return inner_code + cond_code + "JNEG 2\n" + f"JUMP {-inner_len -cond_len - 1}\n"
        if cond_category == "GEQ":
            return inner_code + cond_code + f"JNEG  {-inner_len -cond_len}\n"
        if cond_category == "GE":
            return inner_code + cond_code + "JPOS 2\n" + f"JUMP {-inner_len -cond_len - 1}\n"
        if cond_category == "LEQ":
            return inner_code + cond_code + f"JPOS  {-inner_len -cond_len}\n"

    @_('PIDENTIFIER')
    def iterator(self, p):
        id = p[0]
        id_to = p[0] + "TO"

        if id in self.iter:
            msg = f"Błąd w linii {p.lineno}: druga deklaracja {id}"
            raise Exception(msg)

        if id not in self.regs:
            self.iter[id] = ("mem", self.memtop)
            self.memtop += 1
            self.iter[id_to] = ("mem", self.memtop)
            self.memtop += 1
            return id, id_to
        else:
            self.iter[id] = ("reg", self.regs[id])
            self.iter[id_to] = ("mem", self.memtop)
            self.memtop += 1
            return id, id_to

    @_('FOR iterator FROM value TO value DO commands ENDFOR')
    def command(self, p):
        id, id_to = p[1]
        from_code = p[3][1]
        to_code = p[5][1]
        inner_code = p[7]
        inner_len = inner_code.count('\n')

        if id not in self.regs:
            get_address = self.generateNumber(self.iter[id][1])
            get_address_len = get_address.count("\n")
            get_to_address = self.generateNumber(self.iter[id_to][1])
            get_to_address_len = get_to_address.count("\n")
            load_to_value = get_to_address + "LOAD a\n"
            load_to_value_len = get_to_address_len + 1

            return get_to_address +\
                "SWAP d\n" +\
                to_code +\
                "STORE d\n" +\
                get_address +\
                "SWAP d\n" +\
                from_code +\
                "DEC a\n" +\
                "STORE d\n" +\
                get_address +\
                "SWAP d\n" +\
                "LOAD d\n" +\
                "INC a\n" +\
                "STORE d\n" +\
                "SWAP d\n" +\
                load_to_value +\
                f"SUB d\n" +\
                f"JNEG {inner_len + 2}\n" +\
                inner_code +\
                f"JUMP {-inner_len -load_to_value_len -get_address_len -7}\n", id

        else:
            reg = self.regs[id]
            inner_len = inner_code.count('\n')
            get_to_address = self.generateNumber(self.iter[id_to][1])
            get_to_address_len = get_to_address.count("\n")
            load_to_value = get_to_address + "LOAD a\n"
            load_to_value_len = get_to_address_len + 1

            return get_to_address +\
                "SWAP d\n" +\
                to_code +\
                "STORE d\n" +\
                from_code +\
                "DEC a\n" +\
                f"SWAP {reg}\n" +\
                load_to_value +\
                f"INC {reg}\n" +\
                f"SUB {reg}\n" +\
                f"JNEG {inner_len + 2}\n" +\
                inner_code +\
                f"JUMP {-inner_len -load_to_value_len -3}\n", id

    @_('FOR iterator FROM value DOWNTO value DO commands ENDFOR')
    def command(self, p):
        id, id_to = p[1]
        from_code = p[3][1]
        to_code = p[5][1]
        inner_code = p[7]
        inner_len = inner_code.count('\n')
        to_code_len = to_code.count('\n')

        if id not in self.regs:
            get_address = self.generateNumber(self.iter[id][1])
            get_address_len = get_address.count("\n")
            get_to_address = self.generateNumber(self.iter[id_to][1])
            get_to_address_len = get_to_address.count("\n")
            load_to_value = get_to_address + "LOAD a\n"
            load_to_value_len = get_to_address_len + 1

            return get_to_address +\
                "SWAP d\n" +\
                to_code +\
                "STORE d\n" +\
                get_address +\
                "SWAP d\n" +\
                from_code +\
                "INC a\n" +\
                "STORE d\n" +\
                get_address +\
                "SWAP d\n" +\
                "LOAD d\n" +\
                "DEC a\n" +\
                "STORE d\n" +\
                "SWAP d\n" +\
                load_to_value +\
                f"SUB d\n" +\
                f"JPOS {inner_len + 2}\n" +\
                inner_code +\
                f"JUMP {-inner_len -load_to_value_len -get_address_len -7}\n", id

        else:
            reg = self.regs[id]
            inner_len = inner_code.count('\n')
            to_code_len = to_code.count('\n')

            get_to_address = self.generateNumber(self.iter[id_to][1])
            get_to_address_len = get_to_address.count("\n")
            load_to_value = get_to_address + "LOAD a\n"
            load_to_value_len = get_to_address_len + 1

            return get_to_address +\
                "SWAP d\n" +\
                to_code +\
                "STORE d\n" +\
                from_code +\
                "INC a\n" +\
                f"SWAP {reg}\n" +\
                load_to_value +\
                f"DEC {reg}\n" +\
                f"SUB {reg}\n" +\
                f"JPOS {inner_len + 2}\n" +\
                inner_code +\
                f"JUMP {-inner_len -load_to_value_len -3}\n", id

    @_('READ identifier ";"')
    def command(self, p):
        category, id, code, _ = p[1]
        self.inits.add(id)

        if category == "var_reg":
            return "GET\n" + f"SWAP {self.regs[id]}\n"

        return code + "SWAP b\n" + "GET\n" + "STORE b\n"

    @_('WRITE value ";"')
    def command(self, p):
        return p[1][1] + "PUT\n"

    # loads value to register a
    @_('value')
    def expression(self, p):
        return p[0], None, None

    @_('value PLUS value',
       'value MINUS value',
       'value TIMES value',
       'value DIV value',
       'value MOD value')
    def expression(self, p):
        return p[0], p[1], p[2]

    @_('value EQ value',
       'value NEQ value',
       'value LE value',
       'value GE value',
       'value LEQ value',
       'value GEQ value')
    def condition(self, p):
        return (p[1], self.subtraction(p[0], p[2]))

    # loads value to register a
    @_('NUM')
    def value(self, p):
        return ("num", self.generateNumber(p[0]), p[0])

    # loads value to register a
    @_('identifier')
    def value(self, p):
        category, id, code, lineno = p[0]

        if category != "arr":
            self.checkInit(id, lineno)

        if category == "var_reg":
            return (category, f"RESET a\nADD {self.regs[id]}\n", id)

        return (category, code + "LOAD a\n", id)

    # loads address to register a
    # returns loaded address and generated code
    @_('PIDENTIFIER')
    def identifier(self, p):
        id = p[0]

        self.checkVar(id, p.lineno)

        if id in self.var:
            category, address = self.var[id]
        else:
            category, address = self.iter[id]

        if category == "mem":
            return ("var", id, self.generateNumber(address), p.lineno)
        else:
            # address simply does not exist
            return ("var_reg", id, None, p.lineno)

    @_('PIDENTIFIER "[" NUM "]"')
    def identifier(self, p):
        tab = p[0]
        id = p[2]

        self.checkArr(tab, p.lineno)

        memtop, first, last = self.arr[tab]

        if id < first or id > last:
            msg = f"Błąd w linii {p.lineno}: indeks {id} poza zakresem tablicy {tab}"
            raise Exception(msg)

        return ("arr", tab + str(id), self.generateNumber(memtop + id - first), p.lineno)

    @_('PIDENTIFIER "[" PIDENTIFIER "]"')
    def identifier(self, p):
        tab = p[0]
        id = p[2]

        self.checkArr(tab, p.lineno)
        memtop, first, _ = self.arr[tab]
        self.checkVar(id, p.lineno)
        self.checkInit(id, p.lineno)

        lines = ""
        if id in self.var:
            category, address = self.var[id]
        else:
            category, address = self.iter[id]

        if category == "mem":
            lines += self.generateNumber(address)
            lines += "LOAD a\nSWAP b\n"
        else:
            lines += f"RESET a\nADD {address}\nSWAP b\n"
        lines += self.generateNumber(memtop - first)
        lines += "ADD b\n"

        return ("arr", tab + id, lines, p.lineno)

    def error(self, p):
        msg = f"Błąd w linii {p.lineno}: nierozpoznany napis {p.value}"
        raise Exception(msg)
