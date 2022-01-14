from sly import Lexer
from sys import argv


class TestLexer(Lexer):
    tokens = {DECLARE,
              ASSIGN,
              PLUS, MINUS, TIMES, DIV, MOD,
              EQ, NEQ, GE, GEQ, LE, LEQ,
              LBR, RBR,
              LPA, RPA,
              OTHER}

    @_(r'DECLARE')
    def DECLARE(self, t):
        t.value = "VAR"
        return t

    @_(r':=')
    def ASSIGN(self, t):
        t.value = "ASSIGN"
        return t

    @_(r'\+')
    def PLUS(self, t):
        t.value = "PLUS"
        return t

    @_(r'\-')
    def MINUS(self, t):
        t.value = "MINUS"
        return t

    @_(r'\*')
    def TIMES(self, t):
        t.value = "TIMES"
        return t

    @_(r'\/')
    def DIV(self, t):
        t.value = "DIV"
        return t

    @_(r'\%')
    def MOD(self, t):
        t.value = "MOD"
        return t

    @_(r'=')
    def EQ(self, t):
        t.value = "EQ"
        return t

    @_(r'!=')
    def NEQ(self, t):
        t.value = "NEQ"
        return t

    @_(r'<=')
    def LEQ(self, t):
        t.value = "LEQ"
        return t

    @_(r'>=')
    def GEQ(self, t):
        t.value = "GEQ"
        return t

    @_(r'<')
    def LE(self, t):
        t.value = "LE"
        return t

    @_(r'>')
    def GE(self, t):
        t.value = "GE"
        return t

    @_(r'\(')
    def LPA(self, t):
        t.value = "["
        return t

    @_(r'\)')
    def RPA(self, t):
        t.value = "]"
        return t

    @_(r'\[')
    def LBR(self, t):
        t.value = "("
        return t

    @_(r'\]')
    def RBR(self, t):
        t.value = ")"
        return t

    OTHER = r'.|\r?\n+|\t| '

    def error(self, t):
        print("Illegal character '%s'" % t.value[0])
        self.index += 1


if __name__ == '__main__':
    lexer = TestLexer()

    try:
        fr = open(argv[1], 'r')
        text = fr.read()

        t = lexer.tokenize(text)
        result = ""
        for token in t:
            result += token.value

        fw = open(argv[2], "w")
        fw.write(result)

    except Exception as e:
        print(e)
        exit(1)
