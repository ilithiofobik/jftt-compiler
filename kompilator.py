from lexer import LangLexer
from parser import LangParser
from sys import argv

if __name__ == '__main__':
    lexer = LangLexer()
    parser = LangParser()

    try:
        fr = open(argv[1], 'r')
        text = fr.read()

        # for tok in lexer.tokenize(text):
            #print('type=%r, value=%r' % (tok.type, tok.value))

        parser.optimize_registers(lexer.tokenize(text))
        parsed = parser.parse(lexer.tokenize(text))
        print(parser.var)
        print(parser.arr)
        print(parser.inits)

        if parsed:
            fw = open(argv[2], "w")
            fw.write(parsed)

    except Exception as e:
        print(e)
        exit(1)
