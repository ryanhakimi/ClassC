import unittest

from tokenizer import Tokenizer, TokenizerError, TokenType, tokenize


class TestTokenizer(unittest.TestCase):
    def test_single_character_tokens(self):
        source = "()+-*/<"
        tokens = tokenize(source)
        token_types = [token.token_type for token in tokens]
        token_values = [token.value for token in tokens]

        self.assertEqual(
            token_types,
            [
                TokenType.LEFT_PAREN,
                TokenType.RIGHT_PAREN,
                TokenType.PLUS,
                TokenType.MINUS,
                TokenType.MULTIPLY,
                TokenType.DIVIDE,
                TokenType.LESS_THAN,
            ],
        )
        self.assertEqual(token_values, ["(", ")", "+", "-", "*", "/", "<"])

    def test_assign_and_double_equals(self):
        source = "= =="
        tokens = tokenize(source)

        self.assertEqual(tokens[0].token_type, TokenType.ASSIGN)
        self.assertEqual(tokens[0].value, "=")
        self.assertEqual(tokens[1].token_type, TokenType.DOUBLE_EQUALS)
        self.assertEqual(tokens[1].value, "==")

    def test_keywords(self):
        source = (
            "Int Boolean Void true false this break println while if "
            "return vardec method init super class new call"
        )
        tokens = tokenize(source)
        expected_types = [
            TokenType.INT_TYPE,
            TokenType.BOOLEAN_TYPE,
            TokenType.VOID_TYPE,
            TokenType.TRUE,
            TokenType.FALSE,
            TokenType.THIS,
            TokenType.BREAK,
            TokenType.PRINTLN,
            TokenType.WHILE,
            TokenType.IF,
            TokenType.RETURN,
            TokenType.VARDEC,
            TokenType.METHOD,
            TokenType.INIT,
            TokenType.SUPER,
            TokenType.CLASS,
            TokenType.NEW,
            TokenType.CALL,
        ]

        self.assertEqual([token.token_type for token in tokens], expected_types)
