from sly import Lexer


class LangLexer(Lexer):
    tokens = {VAR, BEGIN, END,
              ASSIGN,
              IF, THEN, ELSE, ENDIF,
              WHILE, DO, ENDWHILE,
              REPEAT, UNTIL,
              FOR, FROM, TO, DOWNTO, ENDFOR,
              READ, WRITE,
              PLUS, MINUS, TIMES, DIV, MOD,
              EQ, NEQ, LE, GE, LEQ, GEQ,
              NUM, PIDENTIFIER}

    literals = {',', '[', ']', '(', ')', ':', ';'}

    ignore = ' \t'

    VAR = r'VAR'
    BEGIN = r'BEGIN'

    ASSIGN = r'ASSIGN'

    IF = r'IF'
    THEN = r'THEN'
    ENDIF = r'ENDIF'

    WHILE = r'WHILE'
    DO = r'DO'
    ENDWHILE = r'ENDWHILE'

    REPEAT = r'REPEAT'
    UNTIL = r'UNTIL'

    FOR = r'FOR'
    FROM = r'FROM'
    TO = r'TO'
    DOWNTO = r'DOWNTO'
    ENDFOR = r'ENDFOR'
    END = r'END'

    READ = r'READ'
    WRITE = r'WRITE'

    PLUS = r'PLUS'
    MINUS = r'MINUS'
    TIMES = r'TIMES'
    DIV = r'DIV'
    MOD = r'MOD'

    EQ = r'EQ'
    NEQ = r'NEQ'
    LE = r'LE'
    GE = r'GE'
    LEQ = r'LEQ'
    GEQ = r'GEQ'

    PIDENTIFIER = r'[_a-z]+'

    @_(r'\(')
    def comment(self, t):
        self.begin(CommLexer)

    @_(r'-?\d+')
    def NUM(self, t):
        t.value = int(t.value)
        return t

    @_(r'\r?\n+')
    def ignore_newline(self, t):
        self.lineno += len(t.value)

    def error(self, t):
        print("Illegal character '%s'" % t.value[0])
        self.index += 1


class CommLexer(Lexer):
    tokens = {}

    ignore = ' \t'

    @_(r'\)')
    def end_comm(self, t):
        self.begin(LangLexer)

    @_(r'[^\)\(]+|\n')
    def ignore_char(self, t):
        pass

    @_(r'\n')
    def ignore_newline(self):
        self.lineno += 1

    def error(self, t):
        print("Błąd: Zagnieżdżone komentarze")
        exit(1)


if __name__ == '__main__':
    lexer = LangLexer()

    while 1:
        try:
            text = input()
        except EOFError:
            break
        if text:
            for tok in lexer.tokenize(text):
                print('type=%r, value=%r' % (tok.type, tok.value))
