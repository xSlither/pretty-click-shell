import click
import re

from pygments.lexer import RegexLexer, bygroups
from pygments.token import (
    Punctuation,
    Text,
    Operator,
    Keyword,
    Name,
    String,
    Number,
    Generic,
    Comment,
    Error
)

from . import globals as globs
from ._completion import COMPLETION_TREE, deep_get



def command_lexer(lexer, match):
    parsed_word = match.group(1)
    
    true_line = globs.__CURRENT_LINE__
    if ' ' in true_line.rstrip():
        begin_line = true_line[0: match.start()]
        parsed_line = true_line[0: (len(begin_line) + len(true_line[match.start():].split(' ')[0]))]
    else: parsed_line = true_line

    line = (((' '.join(globs.__SHELL_PATH__) + ' ') if len(globs.__SHELL_PATH__) else '') + parsed_line).rstrip()

    if ' ' in line: words = line.split(' ')
    else: words = [line]

    if ' ' in true_line: original_words = true_line.rstrip().split(' ')
    else: original_words = [true_line]

    word = words[len(words) - 1]
    lastword = words[len(words) - 2] if len(words) > 1 else None
    priorOption = words[len(words) - 3] if len(words) > 2 else None

    current_key = []
    for i in range(0, len(words)):
        if i < len(globs.__SHELL_PATH__): continue

        try:
            if deep_get(COMPLETION_TREE, *words[:len(words) - i]):
                if len(original_words) > 2: 
                    current_key = words[:(len(words) - (i - 1)) + len(globs.__SHELL_PATH__)]
                elif '--' in words: current_key = words[:len(words) - i] 
                else:
                    current_key = words[:len(words) - (i - 1)]
                    if deep_get(COMPLETION_TREE, *current_key): break

            elif priorOption and '--' in priorOption:
                current_key = words[:len(words) - (i + 1)]
                if deep_get(COMPLETION_TREE, *current_key):  break

            else:
                key = words[:len(words) - (i + 1)]
                if deep_get(COMPLETION_TREE, *key):
                    current_key = key
                    break
        except Exception as e: break

    obj = deep_get(COMPLETION_TREE, *current_key)
    obj2 = deep_get(COMPLETION_TREE, *words)


    def get_parameter_token():
        def get_option(name: str):
            if len(obj['_options']):
                try: return [x for x in obj['_options'] if x[0] == name][0][1]
                except IndexError: pass
            return None

        def get_option_names():
            expression = r'(?<=--)([a-zA-Z0-9]*)(?=\s)'
            return re.findall(expression, line)    

        if len(obj['_options']):
            option = get_option(lastword)
            if option:
                if not (option.is_bool_flag or option.is_flag):
                    values = []
                    isChoice = False

                    if option.type.name == 'choice': 
                        values = [c for c in option.type.choices if c]
                        isChoice = True
                    elif option.choices and ('Choice' in str(type(option.choices))): 
                        values = [c for c in option.choices.choices if c]
                        isChoice = True

                    # Verified Option Parameter
                    if isChoice and word in values: return Name.Attribute
                    elif isChoice: return Name.InvalidCommand
                    else: Text

        if len(obj['_arguments']):
            nargs = len(words) - len(current_key)

            def AnalyzeOptions():
                option_names = get_option_names()
                ret = 0
                for oName in option_names:
                    option = get_option('--%s' % oName)
                    if option:
                        if not (option.is_bool_flag or option.is_flag): ret += 2
                return ret

            nargs = nargs - AnalyzeOptions()
            if nargs <= len(obj['_arguments']):
                arg = obj['_arguments'][nargs - 1 if nargs > 0 else 0]

                name = arg[0]
                argument: PrettyArgument = arg[1]
                values = arg[2]

                isChoice = bool(argument.type.name == 'choice' or argument.choices)

                # Verified Argument Parameter
                if isChoice and word in values: return Name.Attribute
                elif isChoice: return Name.InvalidCommand
                else: Text

        return Text


    if obj and isinstance(obj, dict):
        if obj['isGroup'] and not obj2:
            l = len(words)
            c = len([x for x in words if '--' in x])
            l -= c if c else 0

            root = deep_get(COMPLETION_TREE, *words[0 + (l - 1)])
            if root or line.count(' ') == 0:
                if (root and line.count(' ') == 0) or not root:
                    yield (match.start(), Text, parsed_word) # Unverified shell root command
                    return

            yield (match.start(), Name.InvalidCommand, parsed_word) # Invalid Group Command
        
        elif obj2:
            if obj2['isShell']:
                yield (match.start(), Name.Label, parsed_word) # Command is a Shell
            elif obj2['isGroup']:
                yield (match.start(), Name.Command, parsed_word) # Is a Command Group
            else:
                if parsed_word == 'exit':
                    yield (match.start(), Name.Exit, parsed_word) # Is an Exit Command
                else:
                    yield (match.start(), Name.SubCommand, parsed_word) # Is a verified Command
        else:
            if not obj['isGroup']: yield (match.start(), get_parameter_token() if len(current_key) else Text, parsed_word) # Is an Argument/Parameter
            else: yield (match.start(), Name.InvalidCommand, parsed_word) # Invalid Group Command

        return

    yield (match.start(), Text, parsed_word) # Unverified sub-shell root command


class ShellLexer(RegexLexer):
    name = "Pretty Shell Lexer"
    flags = re.IGNORECASE

    def get_tokens_unprocessed(self, text, stack=('root',)):
        globs.__CURRENT_LINE__ = text
        return super(ShellLexer, self).get_tokens_unprocessed(text, stack)

    tokens = {
        'root': [
            # SQL Queries
            (r"^SELECT\s", Name.Command, str("query")),

            # Shell Commands
            (r'^(\?|help)\s*$', Name.Help),
            (r'^(q|quit|exit)\s*$', Name.Exit),
            (r'^(cls|clear)\s*$', Name.Help),

            # Boolean
            (r"(True|False|true|false)|((?<=\s)y|n(?=\s|$))", Keyword),

            # Symbols / Integers
            (r"\-?[0-9]+", Number.Integer),
            (r"(\||\&|\$|\@|\%|\#|\!|\^|\*|\(|\)|\{|\}|\[|\])", Number.Operator),

            # Commands
            (r"(?<=^)*(((?<=\s)|^)(:?[a-zA-Z_][a-zA-Z0-9_\-]*)($|\s+))", command_lexer),

            # Options
            (r"--(?<=\s--)help+(?=\s|$)", Name.Help),
            (r"-(?<=\s-)h+(?=\s|$)", Name.Help),
            (r"--(?<=\s--)[a-zA-Z0-9]+(?=\s|$)", Name.Tag),

            # Strings
            (r"'(''|[^'])*'", String.Single),
            (r'"(""|[^"])*"', String.Symbol),
            (r"[;:()\[\],\.]", Punctuation),
        ],
        str("query"): [
            (r"\s+", Text),
            (
                r"(ABORT|ABS|ABSOLUTE|ACCESS|ADA|ADD|ADMIN|AFTER|AGGREGATE|"
                r"ALIAS|ALL|ALLOCATE|ALTER|ANALYSE|ANALYZE|AND|ANY|ARE|AS|"
                r"ASC|ASENSITIVE|ASSERTION|ASSIGNMENT|ASYMMETRIC|AT|ATOMIC|"
                r"AUTHORIZATION|AVG|BACKWARD|BEFORE|BEGIN|BETWEEN|BITVAR|"
                r"BIT_LENGTH|BOTH|BREADTH|BY|C|CACHE|CALL|CALLED|CARDINALITY|"
                r"CASCADE|CASCADED|CASE|CAST|CATALOG|CATALOG_NAME|CHAIN|"
                r"CHARACTERISTICS|CHARACTER_LENGTH|CHARACTER_SET_CATALOG|"
                r"CHARACTER_SET_NAME|CHARACTER_SET_SCHEMA|CHAR_LENGTH|CHECK|"
                r"CHECKED|CHECKPOINT|CLASS|CLASS_ORIGIN|CLOB|CLOSE|CLUSTER|"
                r"COALSECE|COBOL|COLLATE|COLLATION|COLLATION_CATALOG|"
                r"COLLATION_NAME|COLLATION_SCHEMA|COLUMN|COLUMN_NAME|"
                r"COMMAND_FUNCTION|COMMAND_FUNCTION_CODE|COMMENT|COMMIT|"
                r"COMMITTED|COMPLETION|CONDITION_NUMBER|CONNECT|CONNECTION|"
                r"CONNECTION_NAME|CONSTRAINT|CONSTRAINTS|CONSTRAINT_CATALOG|"
                r"CONSTRAINT_NAME|CONSTRAINT_SCHEMA|CONSTRUCTOR|CONTAINS|"
                r"CONTINUE|CONVERSION|CONVERT|COPY|CORRESPONTING|COUNT|"
                r"CREATE|CREATEDB|CREATEUSER|CROSS|CUBE|CURRENT|CURRENT_DATE|"
                r"CURRENT_PATH|CURRENT_ROLE|CURRENT_TIME|CURRENT_TIMESTAMP|"
                r"CURRENT_USER|CURSOR|CURSOR_NAME|CYCLE|DATA|DATABASE|"
                r"DATETIME_INTERVAL_CODE|DATETIME_INTERVAL_PRECISION|DAY|"
                r"DEALLOCATE|DECLARE|DEFAULT|DEFAULTS|DEFERRABLE|DEFERRED|"
                r"DEFINED|DEFINER|DELETE|DELIMITER|DELIMITERS|DEREF|DESC|"
                r"DESCRIBE|DESCRIPTOR|DESTROY|DESTRUCTOR|DETERMINISTIC|"
                r"DIAGNOSTICS|DICTIONARY|DISCONNECT|DISPATCH|DISTINCT|DO|"
                r"DOMAIN|DROP|DYNAMIC|DYNAMIC_FUNCTION|DYNAMIC_FUNCTION_CODE|"
                r"EACH|ELSE|ENCODING|ENCRYPTED|END|END-EXEC|EQUALS|ESCAPE|EVERY|"
                r"EXCEPT|ESCEPTION|EXCLUDING|EXCLUSIVE|EXEC|EXECUTE|EXISTING|"
                r"EXISTS|EXPLAIN|EXTERNAL|EXTRACT|FALSE|FETCH|FINAL|FIRST|FOR|"
                r"FORCE|FOREIGN|FORTRAN|FORWARD|FOUND|FREE|FREEZE|FROM|FULL|"
                r"FUNCTION|G|GENERAL|GENERATED|GET|GLOBAL|GO|GOTO|GRANT|GRANTED|"
                r"GROUP|GROUPING|HANDLER|HAVING|HIERARCHY|HOLD|HOST|IDENTITY|"
                r"IGNORE|ILIKE|IMMEDIATE|IMMUTABLE|IMPLEMENTATION|IMPLICIT|IN|"
                r"INCLUDING|INCREMENT|INDEX|INDITCATOR|INFIX|INHERITS|INITIALIZE|"
                r"INITIALLY|INNER|INOUT|INPUT|INSENSITIVE|INSERT|INSTANTIABLE|"
                r"INSTEAD|INTERSECT|INTO|INVOKER|IS|ISNULL|ISOLATION|ITERATE|JOIN|"
                r"KEY|KEY_MEMBER|KEY_TYPE|LANCOMPILER|LANGUAGE|LARGE|LAST|"
                r"LATERAL|LEADING|LEFT|LENGTH|LESS|LEVEL|LIKE|LIMIT|LISTEN|LOAD|"
                r"LOCAL|LOCALTIME|LOCALTIMESTAMP|LOCATION|LOCATOR|LOCK|LOWER|"
                r"MAP|MATCH|MAX|MAXVALUE|MESSAGE_LENGTH|MESSAGE_OCTET_LENGTH|"
                r"MESSAGE_TEXT|METHOD|MIN|MINUTE|MINVALUE|MOD|MODE|MODIFIES|"
                r"MODIFY|MONTH|MORE|MOVE|MUMPS|NAMES|NATIONAL|NATURAL|NCHAR|"
                r"NCLOB|NEW|NEXT|NO|NOCREATEDB|NOCREATEUSER|NONE|NOT|NOTHING|"
                r"NOTIFY|NOTNULL|NULL|NULLABLE|NULLIF|OBJECT|OCTET_LENGTH|OF|OFF|"
                r"OFFSET|OIDS|OLD|ON|ONLY|OPEN|OPERATION|OPERATOR|OPTION|OPTIONS|"
                r"OR|ORDER|ORDINALITY|OUT|OUTER|OUTPUT|OVERLAPS|OVERLAY|OVERRIDING|"
                r"OWNER|PAD|PARAMETER|PARAMETERS|PARAMETER_MODE|PARAMATER_NAME|"
                r"PARAMATER_ORDINAL_POSITION|PARAMETER_SPECIFIC_CATALOG|"
                r"PARAMETER_SPECIFIC_NAME|PARAMATER_SPECIFIC_SCHEMA|PARTIAL|"
                r"PASCAL|PENDANT|PLACING|PLI|POSITION|POSTFIX|PRECISION|PREFIX|"
                r"PREORDER|PREPARE|PRESERVE|PRIMARY|PRIOR|PRIVILEGES|PROCEDURAL|"
                r"PROCEDURE|PUBLIC|READ|READS|RECHECK|RECURSIVE|REF|REFERENCES|"
                r"REFERENCING|REINDEX|RELATIVE|RENAME|REPEATABLE|REPLACE|RESET|"
                r"RESTART|RESTRICT|RESULT|RETURN|RETURNED_LENGTH|"
                r"RETURNED_OCTET_LENGTH|RETURNED_SQLSTATE|RETURNS|REVOKE|RIGHT|"
                r"ROLE|ROLLBACK|ROLLUP|ROUTINE|ROUTINE_CATALOG|ROUTINE_NAME|"
                r"ROUTINE_SCHEMA|ROW|ROWS|ROW_COUNT|RULE|SAVE_POINT|SCALE|SCHEMA|"
                r"SCHEMA_NAME|SCOPE|SCROLL|SEARCH|SECOND|SECURITY|SELECT|SELF|"
                r"SENSITIVE|SERIALIZABLE|SERVER_NAME|SESSION|SESSION_USER|SET|"
                r"SETOF|SETS|SHARE|SHOW|SIMILAR|SIMPLE|SIZE|SOME|SOURCE|SPACE|"
                r"SPECIFIC|SPECIFICTYPE|SPECIFIC_NAME|SQL|SQLCODE|SQLERROR|"
                r"SQLEXCEPTION|SQLSTATE|SQLWARNINIG|STABLE|START|STATE|STATEMENT|"
                r"STATIC|STATISTICS|STDIN|STDOUT|STORAGE|STRICT|STRUCTURE|STYPE|"
                r"SUBCLASS_ORIGIN|SUBLIST|SUBSTRING|SUM|SYMMETRIC|SYSID|SYSTEM|"
                r"SYSTEM_USER|TABLE|TABLE_NAME| TEMP|TEMPLATE|TEMPORARY|TERMINATE|"
                r"THAN|THEN|TIMESTAMP|TIMEZONE_HOUR|TIMEZONE_MINUTE|TO|TOAST|"
                r"TRAILING|TRANSATION|TRANSACTIONS_COMMITTED|"
                r"TRANSACTIONS_ROLLED_BACK|TRANSATION_ACTIVE|TRANSFORM|"
                r"TRANSFORMS|TRANSLATE|TRANSLATION|TREAT|TRIGGER|TRIGGER_CATALOG|"
                r"TRIGGER_NAME|TRIGGER_SCHEMA|TRIM|TRUE|TRUNCATE|TRUSTED|TYPE|"
                r"UNCOMMITTED|UNDER|UNENCRYPTED|UNION|UNIQUE|UNKNOWN|UNLISTEN|"
                r"UNNAMED|UNNEST|UNTIL|UPDATE|UPPER|USAGE|USER|"
                r"USER_DEFINED_TYPE_CATALOG|USER_DEFINED_TYPE_NAME|"
                r"USER_DEFINED_TYPE_SCHEMA|USING|VACUUM|VALID|VALIDATOR|VALUES|"
                r"VARIABLE|VERBOSE|VERSION|VIEW|VOLATILE|WHEN|WHENEVER|WHERE|"
                r"WITH|WITHOUT|WORK|WRITE|YEAR|ZONE)\b",
                Keyword,
            ),
            (
                r"(ARRAY|BIGINT|BINARY|BIT|BLOB|BOOLEAN|CHAR|CHARACTER|DATE|"
                r"DEC|DECIMAL|FLOAT|INT|INTEGER|INTERVAL|NUMBER|NUMERIC|REAL|"
                r"SERIAL|SMALLINT|VARCHAR|VARYING|INT8|SERIAL8|TEXT)\b",
                Name.Builtin,
            ),
            (r"[+*/<>=~!@#%^&|`?-]", Operator),
            (r"[0-9]+", Number.Integer),
            (r"'(''|[^'])*'", String.Single),
            (r'"(""|[^"])*"', String.Symbol),
            (r"[a-zA-Z_][a-zA-Z0-9_]*", Name),
            (r"[;:()\[\],\.]", Punctuation),
        ],
    }