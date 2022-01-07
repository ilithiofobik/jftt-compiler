from os import error
from sly import Parser
from lexer import LangLexer


class LangParser(Parser):
    # AUXILARY FUNCTIONS

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

        self.var[id] = self.memtop
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
        self.var[id] = self.memtop
        self.memtop += 1

    @_('PIDENTIFIER "[" NUM ":" NUM "]"')
    def declarations(self, p):
        id = p[2]
        first = p[4]
        last = p[6]

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

        return code2 + "SWAP d\n" + code1 + "SWAP d\n" + "STORE d\n"

    @_('IF condition THEN commands ELSE commands ENDIF')
    def command(self, p):
        return ""

    @_('IF condition THEN commands ENDIF')
    def command(self, p):
        return ""

    @_('WHILE condition DO commands ENDWHILE')
    def command(self, p):
        return ""

    @_('REPEAT commands UNTIL condition ";"')
    def command(self, p):
        return ""

    @_('FOR PIDENTIFIER FROM value TO value DO commands ENDFOR')
    def command(self, p):
        return ""

    @_('FOR PIDENTIFIER FROM value DOWNTO value DO commands ENDFOR')
    def command(self, p):
        return ""

    #
    @_('READ identifier ";"')
    def command(self, p):
        _, id, code, _ = p[1]
        self.inits.add(id)
        return code + "SWAP b\n" + "GET\n" + "STORE b\n"

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
        category1, code1, val1 = p[0]
        category2, code2, val2 = p[2]

        if category1 == "num" and category2 == "num":
            return self.generateNumber(val1 - val2)

        if category2 == "num" and val2 >= 0 and val2 <= 10:
            return code1 + val2 * "DEC a\n"

        if category2 == "num" and val2 < 0 and val2 >= -10:
            return code1 + -val2 * "INC a\n"

        return code2 + "SWAP d\n" + code1 + "SUB d\n"

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
            "SWAP c\n"+\
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
        pass

    @_('value MOD value')
    def expression(self, p):
        pass

    @_('value EQ value')
    def condition(self, p):
        pass

    @_('value NEQ value')
    def condition(self, p):
        pass

    @_('value LE value')
    def condition(self, p):
        pass

    @_('value GE value')
    def condition(self, p):
        pass

    @_('value LEQ value')
    def condition(self, p):
        pass

    @_('value GEQ value')
    def condition(self, p):
        pass

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

        return ("var", code + "LOAD a\n", None)

    # loads address to register a
    # returns loaded address and generated code
    @_('PIDENTIFIER')
    def identifier(self, p):
        id = p[0]

        if id in self.arr:
            msg = f"Błąd w linii {p.lineno}: niewłaściwe użycie zmiennej tablicowej {id}"
            raise Exception(msg)

        if id not in self.var:
            msg = f"Błąd w linii {p.lineno}: niezadeklarowana zmienna {id}"
            raise Exception(msg)

        return ("var", id, self.generateNumber(self.var[id]), p.lineno)

    @_('PIDENTIFIER "[" NUM "]"')
    def identifier(self, p):
        tab = p[0]
        id = p[2]

        if tab in self.var:
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

        if tab in self.var:
            msg = f"Błąd w linii {p.lineno}: niewłaściwe użycie zmiennej {tab}"
            raise Exception(msg)

        if tab not in self.arr:
            msg = f"Błąd w linii {p.lineno}: niezadeklarowana zmienna tablicowa {tab}"
            raise Exception(msg)

        memtop, first, _ = self.arr[tab]

        if id in self.arr:
            msg = f"Błąd w linii {p.lineno}: niewłaściwe użycie zmiennej {id}"
            raise Exception(msg)

        if id not in self.inits:
            msg = f"Błąd w linii {p.lineno}: użycie niezainicjowanej zmiennej {id}"
            raise Exception(msg)

        lines = self.generateNumber(self.var[id])
        lines += "LOAD a\n SWAP b\n"
        lines += self.generateNumber(memtop - first)
        lines += "ADD b\n"

        return ("arr", tab, lines, p.lineno)

    def error(self, p):
        msg = f"Błąd w linii {p.lineno}: nierozpoznany napis {p.value}"
        raise Exception(msg)
