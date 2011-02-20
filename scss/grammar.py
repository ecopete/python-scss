from pyparsing import Word, Suppress, Literal, alphanums, hexnums, nums, SkipTo, oneOf, ZeroOrMore, Optional, OneOrMore, Forward, cStyleComment, Combine, dblSlashComment, quotedString, Regex, Empty, lineEnd, alphas


# Base css word and literals
EMPTY = Empty()
IDENT = Word(alphas + '_-', alphanums + "_-")
NUMBER = Combine(Optional("-") + Word(nums+'.'))
COMMA, COLON, SEMICOLON = [Literal(c) for c in ",:;"]
OPT_SEMICOLON = Optional(SEMICOLON.suppress())
LACC, RACC, LPAREN, RPAREN = [Suppress(c) for c in "{}()"]
LLACC, LRACC, LBRACK, RBRACK = [Literal(c) for c in "{}[]"]

# Comment
CSS_COMMENT = cStyleComment + Optional(lineEnd)
SCSS_COMMENT = dblSlashComment
COMMENT = CSS_COMMENT | SCSS_COMMENT

# SCSS directives
MIXIN_SYM = Suppress("@mixin")
INCLUDE_SYM = Suppress("@include")
EXTEND_SYM = Suppress("@extend")
IF_SYM = Suppress("@if")
ELSE_SYM = Suppress("@else")
FOR_SYM = Suppress("@for")
DEBUG_SYM = Suppress("@debug")

# Property values
HASH = Word('#', alphanums + "_-")
HEXCOLOR = Suppress("#") + Word(hexnums, min=3, max=8)
NUMBER_VALUE = NUMBER + ( oneOf("em ex px cm mm in pt pc deg %") | EMPTY)
PATH = Word(alphanums + "_-/.", alphanums + "_-./?#&")

# Operators
MATH_OPERATOR = oneOf("+ - / *")
COMBINATOR = oneOf("+ >")
IF_OPERATOR = oneOf("== != <= >= < >")

# Values
VARIABLE = "$" + IDENT
EXPRESSION = Forward()
FUNCTION = IDENT + LPAREN + ZeroOrMore(COMMA.suppress() | EXPRESSION) + RPAREN
INTERPOLATION_VAR = Suppress("#") + LACC + EXPRESSION + RACC
SIMPLE_VALUE = FUNCTION | NUMBER_VALUE | PATH | IDENT | HEXCOLOR | quotedString
VALUE = Optional('-') + ( SIMPLE_VALUE | VARIABLE )
DIV_STRING = SIMPLE_VALUE + OneOrMore(Literal("/") + SIMPLE_VALUE)
PARENS = LPAREN + EXPRESSION + RPAREN
EXPRESSION << ((VALUE | PARENS) + ZeroOrMore(MATH_OPERATOR + ( VALUE | PARENS )))
SEP_VAL_STRING = EXPRESSION + OneOrMore(COMMA.suppress() + EXPRESSION)

# Property values
TERM = ( DIV_STRING | EXPRESSION ) + Optional(COMMA)
EXPR = OneOrMore(TERM) + Optional("!important")
DEC_NAME = Optional("*") + OneOrMore(IDENT | INTERPOLATION_VAR)
DECLARATION = DEC_NAME + COLON + EXPR + OPT_SEMICOLON

# SCSS group of declarations
DECLARESET = Forward()
DECLARESET << DEC_NAME + COLON.suppress() + LACC + OneOrMore(DECLARESET | DECLARATION | COMMENT) + RACC + OPT_SEMICOLON

# Selectors
ELEMENT_NAME = Combine(OneOrMore(IDENT | '&')) | Literal("*")
ATTRIB = LBRACK + SkipTo("]") + RBRACK
CLASS_NAME = Word('.', alphanums + "-_")
PSEUDO = Regex(r':{1,2}[A-Za-z0-9-_]+')

# TODO: Bug this
FILTER = HASH | CLASS_NAME | ATTRIB
SEL_NAME = ELEMENT_NAME + Optional(INTERPOLATION_VAR) + Optional(PSEUDO)
SEL_FILTER = FILTER + Optional(INTERPOLATION_VAR) + Optional(PSEUDO)
SELECTOR = (SEL_NAME + SEL_FILTER) | INTERPOLATION_VAR | SEL_NAME | SEL_FILTER | PSEUDO

SELECTOR_GROUP = SELECTOR + ZeroOrMore(Optional(COMBINATOR) + SELECTOR)
SELECTOR_TREE = SELECTOR_GROUP + ZeroOrMore(COMMA.suppress() + SELECTOR_GROUP)

# @include
INCLUDE = INCLUDE_SYM + IDENT + Optional(LPAREN + ZeroOrMore(COMMA.suppress() | EXPRESSION) + RPAREN) + OPT_SEMICOLON

# @extend
EXTEND = EXTEND_SYM + SELECTOR + OPT_SEMICOLON

# SCSS variable assigment
VAR_DEFINITION = Suppress("$") + IDENT + COLON.suppress() + (SEP_VAL_STRING | EXPRESSION ) + ("!default" | EMPTY) + OPT_SEMICOLON

# Ruleset
RULESET = Forward()
CONTENT = COMMENT | INCLUDE | VAR_DEFINITION | RULESET
RULE_CONTENT = CONTENT | DECLARESET | DECLARATION

# SCSS control directives
IF_CONDITION = EXPRESSION + Optional(IF_OPERATOR + EXPRESSION)
IF_BODY = LACC + ZeroOrMore(RULE_CONTENT) + RACC
ELSE = ELSE_SYM + LACC + ZeroOrMore(RULE_CONTENT) + RACC
IF = IF_SYM + IF_CONDITION + IF_BODY + (ELSE | EMPTY)
FOR_BODY = ZeroOrMore(RULE_CONTENT)
FOR = FOR_SYM + VARIABLE + Suppress("from") + VALUE + (Suppress("through") | Suppress("to")) + VALUE + LACC + FOR_BODY + RACC
DEBUG = DEBUG_SYM + EXPRESSION + OPT_SEMICOLON
CONTROL_DIR = IF | FOR | DEBUG

RULESET << (
    SELECTOR_TREE +
    LACC + ZeroOrMore(RULE_CONTENT | CONTROL_DIR | EXTEND) + RACC )

# SCSS mixin
MIXIN_PARAM = VARIABLE + Optional(COLON.suppress() + EXPRESSION)
MIXIN_PARAMS = LPAREN + ZeroOrMore(COMMA.suppress() | MIXIN_PARAM) + RPAREN
MIXIN = (MIXIN_SYM + IDENT + Optional(MIXIN_PARAMS) +
    LACC + ZeroOrMore(RULE_CONTENT | CONTROL_DIR) + RACC)

# Root elements
IMPORT = "@import" + FUNCTION + OPT_SEMICOLON
MEDIA = "@media" + IDENT + ZeroOrMore(COMMA + IDENT) + LLACC + ZeroOrMore( RULE_CONTENT | MIXIN | CONTROL_DIR ) + LRACC
FONT_FACE = "@font-face" + LLACC + ZeroOrMore(DECLARATION) + LRACC
VARIABLES = ( Literal("@variables") | Literal('@vars') ) + LLACC + ZeroOrMore(VAR_DEFINITION) + RACC
PSEUDO_PAGE = ":" + IDENT
PAGE = "@page" + Optional(IDENT) + Optional(PSEUDO_PAGE) + LLACC + ZeroOrMore(DECLARATION) + LRACC
CHARSET = "@charset" + IDENT + OPT_SEMICOLON

# Css stylesheet
STYLESHEET = ZeroOrMore(
    FONT_FACE
    | CHARSET
    | MEDIA
    | PAGE
    | CONTENT
    | MIXIN
    | IF
    | FOR
    | IMPORT
    | VARIABLES
    | DECLARATION
    | EXPRESSION
)
