"""Language definitions and lexer factory for VibeCoder."""

from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path

from PyQt6.Qsci import (
    QsciLexer,
    QsciLexerBash,
    QsciLexerBatch,
    QsciLexerCMake,
    QsciLexerCPP,
    QsciLexerCSS,
    QsciLexerCSharp,
    QsciLexerCoffeeScript,
    QsciLexerD,
    QsciLexerDiff,
    QsciLexerFortran,
    QsciLexerHTML,
    QsciLexerIDL,
    QsciLexerJSON,
    QsciLexerJava,
    QsciLexerJavaScript,
    QsciLexerLua,
    QsciLexerMASM,
    QsciLexerMakefile,
    QsciLexerNASM,
    QsciLexerMarkdown,
    QsciLexerMatlab,
    QsciLexerOctave,
    QsciLexerPascal,
    QsciLexerPerl,
    QsciLexerProperties,
    QsciLexerPython,
    QsciLexerRuby,
    QsciLexerSQL,
    QsciLexerTCL,
    QsciLexerTeX,
    QsciLexerVHDL,
    QsciLexerVerilog,
    QsciLexerXML,
    QsciLexerYAML,
    QsciScintilla,
)

from vibecoder.keyword_lexer import KeywordLexer
from vibecoder.themes import apply_dark_palette


def _words(text: str) -> tuple[str, ...]:
    return tuple(text.split())


@dataclass(frozen=True)
class LanguageInfo:
    id: str
    label: str
    extensions: tuple[str, ...] = ()
    filenames: tuple[str, ...] = ()
    lexer: str = "plain"
    keywords: tuple[str, ...] = ()
    line_comments: tuple[str, ...] = ()
    block_comments: tuple[tuple[str, str], ...] = ()
    case_insensitive: bool = False
    ident_extra: str = ""


LANGUAGES: tuple[LanguageInfo, ...] = (
    LanguageInfo("ada", "Ada", (".ada", ".adb", ".ads"), lexer="keyword", line_comments=("--",), keywords=_words(
        "abort abs abstract accept access aliased all and array at begin body case constant declare delay delta digits do else elsif end entry exception exit for function generic goto if in interface is limited loop mod new not null of or others out overriding package pragma private procedure protected raise range record rem renames requeue return reverse select separate some subtype synchronized tagged task terminate then type until use when while with xor"
    )),
    LanguageInfo("assembly", "Assembly", (".asm", ".s"), lexer="masm"),
    LanguageInfo("awk", "Awk", (".awk",), lexer="keyword", line_comments=("#",), keywords=_words(
        "BEGIN END break continue delete do else exit for function getline if in next nextfile print printf return while"
    )),
    LanguageInfo("bash", "Bash", (".sh", ".bash"), lexer="bash"),
    LanguageInfo("batch", "Batch", (".bat", ".cmd"), lexer="batch"),
    LanguageInfo("basic", "Basic", (".bas",), lexer="keyword", case_insensitive=True, line_comments=("'",), keywords=_words(
        "and as boolean byref byval call case const dim do each else elseif end endif error exit explicit false for function get global gosub goto if input integer let line loop mod next not or print private public rem return select step string sub then to true until wend while xor"
    )),
    LanguageInfo("c", "C", (".c", ".h"), lexer="cpp"),
    LanguageInfo("cpp", "C++", (".cpp", ".cc", ".cxx", ".hpp", ".hh", ".hxx"), lexer="cpp"),
    LanguageInfo("csharp", "C#", (".cs",), lexer="csharp"),
    LanguageInfo("css", "CSS", (".css",), lexer="css"),
    LanguageInfo("cmake", "CMake", (".cmake",), filenames=("cmakelists.txt",), lexer="cmake"),
    LanguageInfo("clojure", "Clojure", (".clj", ".cljs", ".cljc"), lexer="keyword", line_comments=(";",), ident_extra="-.*!?+/=<>", keywords=_words(
        "def defn defmacro defmethod defmulti defn- defonce defprotocol defrecord defstruct deftype fn if if-let when when-let let loop recur do doseq dotimes for and or not nil true false quote var ns import require refer case cond condp"
    )),
    LanguageInfo("cobol", "COBOL", (".cob", ".cbl"), lexer="keyword", case_insensitive=True, line_comments=("*>",), keywords=_words(
        "accept add alter call cancel close compute continue delete display divide else end end-if evaluate exit go if initialize inspect merge move multiply open perform read return rewrite search set sort start stop string subtract unstring write"
    )),
    LanguageInfo("coffeescript", "CoffeeScript", (".coffee",), lexer="coffee"),
    LanguageInfo("crystal", "Crystal", (".cr",), lexer="keyword", line_comments=("#",), keywords=_words(
        "abstract alias annotation as asm begin break case class def do else elsif end ensure enum extend false for fun if in include instance_sizeof is_a? lib macro module next nil of out pointerof private protected require rescue return select self sizeof struct super then true type typeof uninitialized union unless until when while with yield"
    )),
    LanguageInfo("d", "D", (".d",), lexer="d"),
    LanguageInfo("dart", "Dart", (".dart",), lexer="keyword", line_comments=("//",), block_comments=(("/*", "*/"),), keywords=_words(
        "abstract as assert async await break case catch class const continue covariant default deferred do dynamic else enum export extends extension external factory false final finally for get hide if implements import in interface is late library mixin new null on operator part required rethrow return sealed set show static super switch sync this throw true try typedef var void while with yield"
    )),
    LanguageInfo("diff", "Diff", (".diff", ".patch"), lexer="diff"),
    LanguageInfo("dockerfile", "Dockerfile", (".dockerfile",), filenames=("dockerfile",), lexer="keyword", line_comments=("#",), case_insensitive=True, keywords=_words(
        "FROM RUN CMD LABEL EXPOSE ENV ADD COPY ENTRYPOINT VOLUME USER WORKDIR ARG ONBUILD STOPSIGNAL HEALTHCHECK SHELL"
    )),
    LanguageInfo("elixir", "Elixir", (".ex", ".exs"), lexer="keyword", line_comments=("#",), keywords=_words(
        "alias and after case catch cond def defp defmodule defstruct do else end fn for if import in not or quote raise receive require rescue super try unless use when with"
    )),
    LanguageInfo("elm", "Elm", (".elm",), lexer="keyword", line_comments=("--",), block_comments=(("{-", "-}"),), keywords=_words(
        "if then else case of let in type alias module exposing import as port where True False"
    )),
    LanguageInfo("erlang", "Erlang", (".erl", ".hrl"), lexer="keyword", line_comments=("%",), keywords=_words(
        "after and andalso band begin bnot bor bsl bsr bxor case catch cond div end fun if let not of or orelse query receive rem try when xor"
    )),
    LanguageInfo("fsharp", "F#", (".fs", ".fsi", ".fsx"), lexer="keyword", line_comments=("//",), block_comments=(("(*", "*)"),), keywords=_words(
        "abstract and as assert base begin class default delegate do done downcast downto elif else end exception extern false finally for fun function global if in inherit inline interface internal lazy let match member module mutable namespace new null of open or override private public rec return sig static struct then to true try type upcast use val void when while with yield"
    )),
    LanguageInfo("fortran", "Fortran", (".f", ".f90", ".f95", ".for"), lexer="fortran"),
    LanguageInfo("go", "Go", (".go",), lexer="keyword", line_comments=("//",), block_comments=(("/*", "*/"),), keywords=_words(
        "break case chan const continue default defer else fallthrough for func go goto if import interface map package range return select struct switch type var true false nil iota"
    )),
    LanguageInfo("graphql", "GraphQL", (".graphql", ".gql"), lexer="keyword", line_comments=("#",), keywords=_words(
        "query mutation subscription fragment on type interface union enum scalar input extend schema directive implements true false null"
    )),
    LanguageInfo("groovy", "Groovy", (".groovy", ".gvy"), lexer="keyword", line_comments=("//",), block_comments=(("/*", "*/"),), keywords=_words(
        "as assert break case catch class const continue def default do else enum extends finally for goto if implements import in instanceof interface native new null package return super switch this throw throws trait true false try while"
    )),
    LanguageInfo("haskell", "Haskell", (".hs", ".lhs"), lexer="keyword", line_comments=("--",), block_comments=(("{-", "-}"),), keywords=_words(
        "case class data default deriving do else if import in infix infixl infixr instance let module newtype of then type where forall foreign"
    )),
    LanguageInfo("hlsl", "HLSL", (".hlsl", ".fx"), lexer="cpp"),
    LanguageInfo("html", "HTML", (".html", ".htm"), lexer="html"),
    LanguageInfo("idl", "IDL", (".idl",), lexer="idl"),
    LanguageInfo("ini", "INI", (".ini", ".cfg"), lexer="ini"),
    LanguageInfo("java", "Java", (".java",), lexer="java"),
    LanguageInfo("javascript", "JavaScript", (".js", ".mjs", ".cjs", ".jsx"), lexer="javascript"),
    LanguageInfo("json", "JSON", (".json",), lexer="json"),
    LanguageInfo("julia", "Julia", (".jl",), lexer="keyword", line_comments=("#",), block_comments=(("#=", "=#"),), keywords=_words(
        "abstract baremodule begin break catch const continue do else elseif end export false finally for function global if import let local macro module mutable primitive quote return struct true try type using where while"
    )),
    LanguageInfo("kotlin", "Kotlin", (".kt", ".kts"), lexer="keyword", line_comments=("//",), block_comments=(("/*", "*/"),), keywords=_words(
        "as break class continue do else false for fun if in interface is null object package return super this throw true try typealias typeof val var when while by catch constructor delegate dynamic field file finally get import init internal out override private protected public reified sealed set typealias where actual abstract annotation companion const crossinline data enum expect external final infix inline inner internal lateinit noinline open operator out override private protected public sealed suspend tailrec vararg"
    )),
    LanguageInfo("latex", "LaTeX", (".tex", ".latex"), lexer="tex"),
    LanguageInfo("lisp", "Lisp", (".lisp", ".lsp", ".cl"), lexer="keyword", line_comments=(";",), ident_extra="-.*!?+/=<>", keywords=_words(
        "defun defmacro defmethod defvar defparameter defconstant defgeneric defclass defstruct lambda let let* if when unless cond case progn prog1 prog2 loop do dolist dotimes and or not nil t quote setq setf car cdr cons list append mapcar funcall apply return values"
    )),
    LanguageInfo("lua", "Lua", (".lua",), lexer="lua"),
    LanguageInfo("makefile", "Makefile", (".mak", ".mk"), filenames=("makefile", "gnumakefile"), lexer="makefile"),
    LanguageInfo("markdown", "Markdown", (".md", ".markdown", ".mdown"), lexer="markdown"),
    LanguageInfo("matlab", "Matlab", (".m",), lexer="matlab"),
    LanguageInfo("nasm", "NASM", (".nasm",), lexer="nasm"),
    LanguageInfo("nim", "Nim", (".nim",), lexer="keyword", line_comments=("#",), keywords=_words(
        "addr and as asm bind block break case cast concept const continue converter defer discard distinct div do elif else end enum except export finally for from func if import in include interface is isnot iterator let macro method mixin mod nil not notin object of or out proc ptr raise ref return shl shr static template try tuple type using var when while xor yield"
    )),
    LanguageInfo("ocaml", "OCaml", (".ml", ".mli"), lexer="keyword", block_comments=(("(*", "*)"),), keywords=_words(
        "and as assert asr begin class constraint do done downto else end exception external false for fun function functor if in include inherit initializer land lazy let lor lsl lsr lxor match method mod module mutable new object of open or private rec sig struct then to true try type val virtual when while with"
    )),
    LanguageInfo("objectivec", "Objective-C", (".mm",), lexer="cpp"),
    LanguageInfo("octave", "Octave", (".octave",), lexer="octave"),
    LanguageInfo("pascal", "Pascal", (".pas", ".pp"), lexer="pascal"),
    LanguageInfo("perl", "Perl", (".pl", ".pm"), lexer="perl"),
    LanguageInfo("php", "PHP", (".php",), lexer="html"),
    LanguageInfo("powershell", "PowerShell", (".ps1", ".psm1", ".psd1"), lexer="keyword", case_insensitive=True, line_comments=("#",), block_comments=(("<#", "#>"),), keywords=_words(
        "begin break catch class continue data do dynamicparam else elseif end enum exit filter finally for foreach from function if in param process return switch throw trap try until while"
    )),
    LanguageInfo("prolog", "Prolog", (".pro", ".prolog"), lexer="keyword", line_comments=("%",), block_comments=(("/*", "*/"),), keywords=_words(
        "is fail true false not once repeat cut assert retract consult dynamic multifile discontiguous"
    )),
    LanguageInfo("python", "Python", (".py", ".pyw", ".pyi"), lexer="python"),
    LanguageInfo("qsharp", "Q#", (".qs",), lexer="keyword", line_comments=("//",), keywords=_words(
        "namespace open operation function body adjoint controlled let mutable use borrow if elif else for in repeat until while return fail within apply new newtype"
    )),
    LanguageInfo("qiskit", "Qiskit", (), lexer="python"),
    LanguageInfo("qml", "QML", (".qml",), lexer="keyword", line_comments=("//",), block_comments=(("/*", "*/"),), keywords=_words(
        "import as property signal function readonly alias required pragma if else for while do switch case default return break continue true false"
    )),
    LanguageInfo("r", "R", (".r",), lexer="keyword", line_comments=("#",), keywords=_words(
        "if else repeat while function for in next break TRUE FALSE NULL Inf NaN NA NA_integer_ NA_real_ NA_complex_ NA_character_"
    )),
    LanguageInfo("racket", "Racket", (".rkt",), lexer="keyword", line_comments=(";",), block_comments=(("#|", "|#"),), ident_extra="-.*!?+/=<>", keywords=_words(
        "define define-syntax lambda let let* letrec if cond else case and or not begin quote quasiquote unquote module require provide struct for for/list match when unless"
    )),
    LanguageInfo("ruby", "Ruby", (".rb",), lexer="ruby"),
    LanguageInfo("rust", "Rust", (".rs",), lexer="keyword", line_comments=("//",), block_comments=(("/*", "*/"),), keywords=_words(
        "as async await break const continue crate dyn else enum extern false fn for if impl in let loop match mod move mut pub ref return self Self static struct super trait true type unsafe use where while abstract become box do final macro override priv typeof unsized virtual yield try"
    )),
    LanguageInfo("sass", "Sass", (".scss", ".sass"), lexer="css"),
    LanguageInfo("scala", "Scala", (".scala", ".sc"), lexer="keyword", line_comments=("//",), block_comments=(("/*", "*/"),), keywords=_words(
        "abstract case catch class def do else extends false final finally for forSome if implicit import lazy match new null object override package private protected return sealed super this throw trait true try type val var while with yield"
    )),
    LanguageInfo("scheme", "Scheme", (".scm", ".ss"), lexer="keyword", line_comments=(";",), block_comments=(("#|", "|#"),), ident_extra="-.*!?+/=<>", keywords=_words(
        "define lambda let let* letrec if cond else case and or not begin quote quasiquote unquote set! do delay force call/cc call-with-current-continuation"
    )),
    LanguageInfo("solidity", "Solidity", (".sol",), lexer="keyword", line_comments=("//",), block_comments=(("/*", "*/"),), keywords=_words(
        "pragma solidity contract interface library function modifier event error struct enum mapping address bool string bytes uint int public private internal external pure view payable returns return if else for while do break continue new delete emit require revert assert try catch import is using memory storage calldata constant immutable override virtual indexed anonymous constructor receive fallback true false"
    )),
    LanguageInfo("sql", "SQL", (".sql",), lexer="sql"),
    LanguageInfo("swift", "Swift", (".swift",), lexer="keyword", line_comments=("//",), block_comments=(("/*", "*/"),), keywords=_words(
        "associatedtype break case catch class continue default defer deinit do else enum extension fallthrough false fileprivate for func guard if import in indirect infix init inout internal is lazy let mutating nil open operator optional override postfix precedencegroup prefix private protocol public repeat required rethrows return right self Self static struct subscript super switch throw throws true try typealias unowned var weak where while"
    )),
    LanguageInfo("tcl", "Tcl", (".tcl",), lexer="tcl"),
    LanguageInfo("toml", "TOML", (".toml",), lexer="keyword", line_comments=("#",), keywords=_words("true false")),
    LanguageInfo("typescript", "TypeScript", (".ts", ".tsx", ".mts", ".cts"), lexer="keyword", line_comments=("//",), block_comments=(("/*", "*/"),), keywords=_words(
        "abstract as asserts async await break case catch class const continue debugger declare default delete do else enum export extends false finally for from function get if implements import in infer instanceof interface is keyof let module namespace never new null of package private protected public readonly require return set static super switch this throw true try type typeof undefined var void while with yield"
    )),
    LanguageInfo("unrealscript", "UnrealScript", (".uc",), lexer="keyword", line_comments=("//",), block_comments=(("/*", "*/"),), keywords=_words(
        "class extends function event state defaultproperties var local if else for while do switch case break continue return new none true false const enum struct replication reliable unreliable simulated"
    )),
    LanguageInfo("verilog", "Verilog", (".v", ".vh", ".sv"), lexer="verilog"),
    LanguageInfo("vhdl", "VHDL", (".vhd", ".vhdl"), lexer="vhdl"),
    LanguageInfo("vim", "Vim script", (".vim",), lexer="keyword", line_comments=('"',), keywords=_words(
        "function endfunction if else elseif endif for endfor while endwhile return let unlet call execute echo set autocmd command map nnoremap inoremap vnoremap syntax highlight"
    )),
    LanguageInfo("visualbasic", "Visual Basic", (".vb",), lexer="keyword", case_insensitive=True, line_comments=("'",), keywords=_words(
        "AddHandler AddressOf Alias And AndAlso As Boolean ByRef ByVal Call Case Catch Class Const Continue Declare Default Delegate Dim DirectCast Do Each Else ElseIf End Enum Erase Error Event Exit False Finally For Friend Function Get GetType Global GoSub GoTo Handles If Implements Imports In Inherits Integer Interface Is IsNot Let Lib Like Loop Me Mod Module MustInherit MustOverride MyBase MyClass Namespace Narrowing New Next Not Nothing NotInheritable NotOverridable Object Of On Operator Option Optional Or OrElse Overloads Overridable Overrides ParamArray Partial Private Property Protected Public RaiseEvent ReadOnly ReDim REM RemoveHandler Resume Return Select Set Shadows Shared Single Static Step Stop String Structure Sub SyncLock Then Throw To True Try TryCast TypeOf Using Variant Wend When While Widening With WithEvents WriteOnly Xor"
    )),
    LanguageInfo("webassembly", "WebAssembly", (".wat", ".wast"), lexer="keyword", line_comments=(";;",), block_comments=(("(;", ";)"),), keywords=_words(
        "module func param result export import memory table global local call call_indirect i32 i64 f32 f64 if else end block loop br br_if return drop nop"
    )),
    LanguageInfo("wolfram", "Wolfram", (".wl", ".wls"), lexer="keyword", block_comments=(("(*", "*)"),), keywords=_words(
        "Module Block With If While For Do Function Table Map Apply Select Cases Replace ReplaceAll SetDelayed Pattern True False Null"
    )),
    LanguageInfo("xml", "XML", (".xml", ".svg", ".xsl"), lexer="xml"),
    LanguageInfo("xaml", "XAML", (".xaml",), lexer="xml"),
    LanguageInfo("yaml", "YAML", (".yaml", ".yml"), lexer="yaml"),
    LanguageInfo("zig", "Zig", (".zig",), lexer="keyword", line_comments=("//",), keywords=_words(
        "addrspace align allowzero and anyframe anytype asm async await break callconv catch comptime const continue defer else enum errdefer error export extern fn for if inline linksection noalias nosuspend noinline null opaque or orelse packed pub resume return struct suspend switch test threadlocal try union unreachable usingnamespace var volatile while"
    )),
    LanguageInfo("zsh", "Zsh", (".zsh",), lexer="bash"),
    LanguageInfo("plain", "Plain Text", (".txt",), lexer="plain"),
)

_NATIVE = {
    "bash": QsciLexerBash,
    "batch": QsciLexerBatch,
    "cmake": QsciLexerCMake,
    "cpp": QsciLexerCPP,
    "csharp": QsciLexerCSharp,
    "css": QsciLexerCSS,
    "coffee": QsciLexerCoffeeScript,
    "d": QsciLexerD,
    "diff": QsciLexerDiff,
    "fortran": QsciLexerFortran,
    "html": QsciLexerHTML,
    "idl": QsciLexerIDL,
    "ini": QsciLexerProperties,
    "java": QsciLexerJava,
    "javascript": QsciLexerJavaScript,
    "json": QsciLexerJSON,
    "lua": QsciLexerLua,
    "makefile": QsciLexerMakefile,
    "masm": QsciLexerMASM,
    "nasm": QsciLexerNASM,
    "markdown": QsciLexerMarkdown,
    "matlab": QsciLexerMatlab,
    "octave": QsciLexerOctave,
    "pascal": QsciLexerPascal,
    "perl": QsciLexerPerl,
    "python": QsciLexerPython,
    "ruby": QsciLexerRuby,
    "sql": QsciLexerSQL,
    "tcl": QsciLexerTCL,
    "tex": QsciLexerTeX,
    "verilog": QsciLexerVerilog,
    "vhdl": QsciLexerVHDL,
    "xml": QsciLexerXML,
    "yaml": QsciLexerYAML,
}

_BY_ID: dict[str, LanguageInfo] = {lang.id: lang for lang in LANGUAGES}

_EXTENSION_MAP: dict[str, str] = {}
_FILENAME_MAP: dict[str, str] = {}
for lang in LANGUAGES:
    for ext in lang.extensions:
        _EXTENSION_MAP[ext.lower()] = lang.id
    for name in lang.filenames:
        _FILENAME_MAP[name.lower()] = lang.id


def language_for_path(path: str | Path | None) -> str:
    if not path:
        return "plain"
    file_path = Path(path)
    by_name = _FILENAME_MAP.get(file_path.name.lower())
    if by_name:
        return by_name
    return _EXTENSION_MAP.get(file_path.suffix.lower(), "plain")


def create_lexer(language_id: str, editor: QsciScintilla) -> QsciLexer | None:
    """Create a lexer for the given language and apply the dark palette."""
    info = _BY_ID.get(language_id)
    if info is None or info.lexer == "plain":
        return None

    lexer: QsciLexer
    if info.lexer == "keyword":
        lexer = KeywordLexer(
            editor,
            name=info.label,
            keywords=info.keywords,
            line_comments=info.line_comments,
            block_comments=info.block_comments,
            case_insensitive=info.case_insensitive,
            ident_extra=info.ident_extra,
        )
    else:
        lexer = _NATIVE[info.lexer](editor)

    apply_dark_palette(lexer)
    return lexer


def label_for_language(language_id: str) -> str:
    info = _BY_ID.get(language_id)
    return info.label if info else "Plain Text"
