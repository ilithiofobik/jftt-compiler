from lexer import LangLexer
from parser import LangParser
from sys import argv, stderr

if __name__ == '__main__':
    lexer = LangLexer()
    parser = LangParser()

    try:
        fr = open(argv[1], 'r')
        text = fr.read()

        parser.optimize_registers(lexer.tokenize(text))
        parsed = parser.parse(lexer.tokenize(text))

        if parsed:
            fw = open(argv[2], "w")
            fw.write(parsed)

    except Exception as e:
        print(e, file=stderr)
        exit(1)
