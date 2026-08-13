# Does a symbol-addressed edit vocabulary survive Java?

## HEADLINE

`"Outer.Inner.method"` is **NOT sufficient** for Java. It fails on three independent axes,
two of which Python and Go let you skip entirely.

Minimum viable address (recommendation):

    com.example.Outer.Inner#process(String,int)

owner-path `#` member `(` source-spelled erased param types `)`.
Parens present = method/constructor; parens absent = field.

And one category is **unaddressable by any string in any surveyed tool**: members of
anonymous classes, local classes, and lambda bodies. Every scheme addresses them
**positionally** (a declaration-order ordinal), which renumbers when the model inserts code
above them — i.e. broken by construction for an edit vocabulary. Refuse the address; fall
back to whole-file (the mechanism this repo already chose in E-D1).

## 1. The positional-ordinal finding (the single most important result)

Three independent, mature systems all fall back to source-declaration-order ordinals.

**(a) JLS 13.1 — binary names.** Anonymous class = enclosing binary name + `$` + digits;
local class = + `$` + digits + simple name.
  - `Outer$Inner` (member), `Outer$1LocalClass` (local), `Outer$1` (anonymous)
  - The digits are a compiler implementation detail, assigned in declaration order.
  https://docs.oracle.com/javase/specs/jls/se21/html/jls-13.html

**(b) Eclipse JDT — anonymous types have NO NAME.** In
`org.eclipse.jdt.internal.core.SourceType`, `isAnonymous()` is literally
`this.name.length() == 0`. Identity comes from `public int localOccurrenceCount = 1`, and
`getOccurrenceCountSignature()` returns that count. The memento appends `JEM_COUNT` (`'!'`)
+ the count. Occurrence counts start at 1 = first in source order.
  source: eclipse-jdt/eclipse.jdt.core `model/org/eclipse/jdt/internal/core/SourceType.java`

**(c) SemanticDB / scip-java — even OVERLOADS are positional.** Verbatim from the spec, the
Java disambiguator is computed from "non-static overloads first, following the same order as
they appear in the original source, static overloads secondly, following the same order as
they appear in the original source"; tag is empty for the first, `+1` for the second, `+2`
for the third. Spec's own example, class `C` with three `m3`:
  - `a/C#m3().`   (non-static, first)
  - `a/C#m3(+1).` (non-static, second)
  - `a/C#m3(+2).` (static, first static)
  https://scalameta.org/docs/semanticdb/specification.html

  => **SCIP is disqualified as our address format.** Adding an overload above renumbers the
  ones below. An edit vocabulary whose addresses shift as a side effect of its own edits is
  not an address format.

**(d) OpenRewrite — anonymous-class methods are not matchable at all.** The only declaration
overload is `MethodMatcher.matches(J.MethodDeclaration method, J.ClassDeclaration enclosing)`.
An anonymous class in the LST is a `J.NewClass` whose `getBody()` returns a **`J.Block`**,
not a `J.ClassDeclaration` — so there is no value to pass as `enclosing`. The source has no
special handling for the anonymous case.
  https://github.com/openrewrite/rewrite/blob/main/rewrite-java/src/main/java/org/openrewrite/java/MethodMatcher.java

## 2. Scheme-by-scheme syntax (all verified against source/spec)

### OpenRewrite MethodMatcher (AspectJ-style)
Form: `<fully-qualified declaring type> <method name>(<arg types>)`, or `#` in place of the
space. Wildcards: `*` = exactly one element, `..` = zero or more.
```
org.foo.Bar baz(String, int)
org.Foo#bar()
java.lang.String substring(..)
org.Foo <constructor>(..)          // constructor
org.Foo <init>(..)                 // constructor, alt spelling
*..* *(String...)                  // any varargs method on any class
org.openrewrite.java.* foo(..)     // that package only, not subpackages
```
Arrays literal (`Object[]`); varargs as `Object...`, `Object[]`, or `..`. Types fully
qualified, case-sensitive.
  https://docs.openrewrite.org/reference/method-patterns

### Javadoc `@see` / `{@link}`
Form: `module/package.class#member(argument-types)`.
```
{@link String#replaceAll(String, String)}
{@link #getComponentAt(int, int) getComponentAt}
ClassName(int, String)             // constructor: class simple name, not "new"
```
Param list may be omitted **only if** not overloaded AND the name isn't also a field/enum
member — i.e. the spec itself makes the paren-suffix the field/method discriminator.
Argument types use **simple names resolved through the compilation unit's imports** (scope-
dependent, not canonical). Member may NOT be a nested class.
  https://docs.oracle.com/en/java/javase/21/docs/specs/javadoc/doc-comment-spec.html

### JVM descriptors (JVMS 4.3.2 / 4.3.3)
BaseType: `B C D F I J S Z`; ObjectType `L<binary name with '/'>;`; ArrayType `[`.
`MethodDescriptor: ( {ParameterDescriptor} ) ReturnDescriptor`, `V` = void.
```
Object m(int, double, Thread)   ->  (IDLjava/lang/Thread;)Ljava/lang/Object;
void doSomething()              ->  ()V
int[] f(String, boolean)        ->  (Ljava/lang/String;Z)[I
double[][][]                    ->  [[[D
constructor <init>()            ->  ()V
```
Fully erased. Generic info lives separately in the `Signature` attribute (4.7.9):
`<T:Ljava/lang/Object;>(TT)Ljava/util/Optional<TT;>;`.
  https://docs.oracle.com/javase/specs/jvms/se21/html/jvms-4.html
Descriptors include the **return type**, so they over-disambiguate relative to source-level
overload resolution — fine for identity, wasteful for an emitter.

### Eclipse JDT handle identifiers — the real canonical-address format
`IJavaElement.getHandleIdentifier()` <-> `JavaCore.create(String)`; "stable across workspace
sessions". **But the Javadoc explicitly says "The format of the string is not specified."**
It is a stable opaque token, not a public grammar. Do not have a model emit one.
  https://help.eclipse.org/latest/topic/org.eclipse.jdt.doc.isv/reference/api/org/eclipse/jdt/core/IJavaElement.html

The delimiters, from `JavaElement.java` (eclipse-jdt/eclipse.jdt.core):

| Constant | Char | Constant | Char |
|---|---|---|---|
| JEM_ESCAPE | `\` | JEM_TYPE | `[` |
| JEM_JAVAPROJECT | `=` | JEM_PACKAGEDECLARATION | `%` |
| JEM_PACKAGEFRAGMENTROOT | `/` | JEM_IMPORTDECLARATION | `#` |
| JEM_PACKAGEFRAGMENT | `<` | JEM_COUNT | `!` |
| JEM_FIELD | `^` | JEM_LOCALVARIABLE | `@` |
| JEM_METHOD | `~` | JEM_TYPE_PARAMETER | `]` |
| JEM_INITIALIZER | `\|` | JEM_ANNOTATION | `}` |
| JEM_COMPILATIONUNIT | `{` | JEM_LAMBDA_EXPRESSION | `)` |
| JEM_CLASSFILE | `(` | JEM_LAMBDA_METHOD | `&` |
| JEM_MODULAR_CLASSFILE | `'` | JEM_STRING | `"` |
| JEM_MODULE | `` ` `` | | |

Real handle for `fooPackage.barPackage.FooClass.fooMethod(int)` in project `FooProject`,
source folder `src`:

    =FooProject/src<fooPackage.barPackage{FooClass.java[FooClass~fooMethod~I

(via WALA's `JdtUtil` javadoc, https://wala.github.io/javadoc/com/ibm/wala/ide/util/JdtUtil.html)

Construction, from `SourceMethod.getHandleMemento`: parent memento, then `~` + escaped
method name, then **`~` + each parameter type**, then `!` + occurrence count if > 1.
Note `^` = field vs `~` = method — JDT encodes the kind in the delimiter.

Parameter types are **JDT `Signature` strings, not JVM descriptors** — and for *source*
elements they are **unresolved** `Q` forms:

| JDT Signature | Meaning |
|---|---|
| `I` | int |
| `[[I` | int[][] |
| `QString;` | `String` **as written in source** (unresolved) |
| `Ljava.lang.String;` | resolved form — note **dots**, not slashes |
| `[QString;` | `String[]` (source) |
| `TT;` | type variable T |

  https://help.eclipse.org/latest/topic/org.eclipse.jdt.doc.isv/reference/api/org/eclipse/jdt/core/Signature.html

The `Q` form is significant: **JDT's own canonical address for a source method records the
parameter types exactly as spelled in the file**, not canonicalised. That validates
source-spelling matching (see §5).

### SCIP / scip-java
```
<symbol>               ::= <scheme> ' ' <package> ' ' (<descriptor>)+ | 'local ' <local-id>
<package>              ::= <manager> ' ' <package-name> ' ' <version>
<namespace>            ::= <name> '/'
<type>                 ::= <name> '#'
<term>                 ::= <name> '.'
<method>               ::= <name> '(' (<method-disambiguator>)? ').'
<type-parameter>       ::= '[' <name> ']'
<parameter>            ::= '(' <name> ')'
```
e.g. `com/example/MyClass#myMethod(+1).`; locals are `local <id>`, "must not be referenced
outside their Document."
  https://github.com/scip-code/scip/blob/main/docs/scip.md

## 3. THE HARD CASES MATRIX

| | Javadoc `#` ref | JVM descriptor | JDT handle | OpenRewrite MethodMatcher | SCIP |
|---|---|---|---|---|---|
| **(a) `foo(int)` vs `foo(String)`** | `C#foo(int)` / `C#foo(String)` — simple names, import-scoped | `(I)V` / `(Ljava/lang/String;)V` — erased, +return type | `~foo~I` / `~foo~QString;` — source-spelled `Q` form | `com.C foo(int)` / `com.C foo(java.lang.String)` — FQ | `C#foo().` / `C#foo(+1).` — **POSITIONAL** |
| **(b) method on INNER class** | `Outer.Inner#m()` (dots) | `Outer$Inner.m` (`$`) | `[Outer[Inner~m` — nested `[` | `com.Outer.Inner m()`; `TypeUtils.fullyQualifiedNamesAreEqual` reconciles `.` vs `$` | `Outer#Inner#m().` |
| **(c) method on ANONYMOUS class** | **impossible** — member may not be a nested class, and there is no name | `Outer$1.m` — **positional digits** | empty type name + `!N` occurrence count — **positional** | **impossible** — no `J.ClassDeclaration` to pass to `matches()` | `local <id>` — document-scoped, non-portable |
| **(d) generic `<T> void foo(T)`** | `#foo(T)` — type var by source name | `(Ljava/lang/Object;)V` erased; `Signature` attr carries `<T:...>(TT)V` | `~foo~TT;` (type-var sig) | erased bound; matching generics is a known pain point (rewrite discussion #5038) | `foo().` + `[T]` type-param descriptor |
| **(e) constructor** | `ClassName(int, String)` — class simple name | `<init>` + `()V` | method whose name == type simple name | `org.Foo <constructor>(..)` or `org.Foo <init>(..)` | `#<init>().` |
| **(f) field vs method, same name** | parens present/absent — spec makes this explicit | field desc vs method desc are disjoint grammars | `^name` vs `~name` — different delimiter char | matcher is methods-only; fields out of scope | `name.` (term) vs `name().` (method) |
| **(g) record compact constructor** | no distinct syntax — collides with canonical ctor | `<init>` + canonical param descriptor (compiler synthesises the params) | modeled as a method; JDT AST `MethodDeclaration` grammar covers compact ctors (JLS16), which "omit explicit parameters" | no distinct syntax | no distinct syntax |
| **(h) annotations in the span?** | n/a | n/a | **YES — annotations are `ExtendedModifier`s inside `MethodDeclaration`** | **YES — `leadingAnnotations` is a field of `J.MethodDeclaration`** | n/a |

**(g) is a genuine hole.** No addressing scheme surveyed distinguishes a record's compact
constructor from its canonical constructor, because at the binary level they are the same
`<init>`. Only the *source* AST distinguishes them, and only in JavaParser, which has a
dedicated node type `CompactConstructorDeclaration`
(https://github.com/javaparser/javaparser). Our schema must invent a marker, e.g.
`Point#<compact>()`.

## 4. SPAN-WITH-ATTACHMENTS — Java is BETTER than Python and Go, not worse

The task premise ("Java has both problems at once") is **wrong, and this is good news.**

**Annotations are not Python decorators.** In Java, annotations are *modifiers* — they are
syntactically inside the declaration by grammar. JDT's `MethodDeclaration` production:

    MethodDeclaration:
        [ Javadoc ] { ExtendedModifier } [ < TypeParameter ... > ]
        ( Type | void ) Identifier ( ... ) ...

So annotations can never be orphaned by replacing the method node — they are part of it.
Python's `ast.FunctionDef.lineno` points at `def`, excluding decorators; Java has no
analogous gap.
  https://help.eclipse.org/latest/topic/org.eclipse.jdt.doc.isv/reference/api/org/eclipse/jdt/core/dom/MethodDeclaration.html

**Javadoc IS inside the JDT node span.** The same production has `[ Javadoc ]` as a *child*,
and the JDT source-range rule is explicit:
  - *with* Javadoc: the range **begins at the opening `/**` delimiter**;
  - *without*: at the first modifier keyword, else `<`, else return type, else the identifier;
  - and always extends through the final `;` or the closing brace of the body.

So `ASTNode.getStartPosition()` / `getLength()` on a JDT `MethodDeclaration` already yields
**exactly the unit we want to replace**: Javadoc + annotations + modifiers + generics +
signature + body. **This is the only tool surveyed where the natural node span is the
replaceable unit.** Neither Python `ast` nor Go `ast` does this.

**`getExtendedStartPosition` covers the remaining case.**
`CompilationUnit.getExtendedStartPosition(ASTNode)` / `getExtendedLength(ASTNode)`:
"the extended source range may include comments and whitespace immediately before or after
the normal source range for the node." That picks up non-Javadoc leading comments (`// TODO`
above the method) and trailing comments.
  https://help.eclipse.org/latest/topic/org.eclipse.jdt.doc.isv/reference/api/org/eclipse/jdt/core/dom/CompilationUnit.html

**OpenRewrite: annotations in the node, Javadoc in the prefix.** `J.MethodDeclaration` has a
`leadingAnnotations` field (confirmed for the sibling `J.ClassDeclaration` in `J.java`, which
declares `leadingAnnotations`, `modifiers`, `typeParameters`, `name`, `extendings`,
`implementings`, `permitting`, `body`, `type`). Comments live in `Space`:
> "Wherever whitespace can occur in Java, so can comments (at least block and javadoc style
> comments). So whitespace and comments are like peanut butter and jelly."
`Space` = `{ String whitespace; List<Comment> comments; }`. A Javadoc before a method is a
`Comment` in that method's **prefix `Space`** — so it IS reachable from the node, but you
must deliberately preserve `getPrefix()` when swapping the node or you drop it.
  https://github.com/openrewrite/rewrite/blob/main/rewrite-java/src/main/java/org/openrewrite/java/tree/Space.java

**javac Trees: Javadoc is a SEPARATE API — same orphaning bug as Python/Go.**
`SourcePositions.getStartPosition` operates on `Tree` nodes; doc comments are reached only
via `DocTrees.getDocCommentTree(TreePath)` and positioned via `DocSourcePositions`. A method's
`getStartPosition` therefore excludes its Javadoc.
  https://docs.oracle.com/en/java/javase/17/docs/api/jdk.compiler/com/sun/source/util/DocSourcePositions.html

**Spoon: separate, and undocumented on this point.** `CtMethod` has `getPosition()`
(SourcePosition) *and* separately `getDocComment()` / `getComments()` / `getAnnotations()`.
The Spoon docs do not state whether an element's `SourcePosition` includes leading comments.
**UNVERIFIED — needs an empirical check if Spoon is chosen.**
  https://spoon.gforge.inria.fr/comments.html

**JavaParser: annotations are children of the node (so in `getRange()`); Javadoc is a separate
`Comment` node with its own `getRange()`, attached via `getComment()`.** Known asymmetry:
javadoc placed *below* an annotation is not picked up as the method's comment
(javaparser/javaparser#40). **PARTIALLY VERIFIED — the exact inclusion boundary of
`MethodDeclaration.getRange()` should be confirmed with a 10-minute empirical test before
relying on it.**

## 5. WHAT JAVA FORCES THAT PYTHON AND GO LET YOU AVOID

1. **Overload disambiguation — unavoidable.** Python and Go have no overloading, so
   `Class.method` / `Receiver.Method` is unique by construction. Java requires a parameter
   list in the address. This is the axis that kills the naive scheme outright.

2. **Choosing the *spelling* of parameter types — a new decision with no Python/Go analogue.**
   Four incompatible conventions exist for the same method: `foo(String)` (Javadoc, import-
   scoped), `foo(java.lang.String)` (OpenRewrite, FQ), `(Ljava/lang/String;)V` (JVM, slashes),
   `~foo~QString;` (JDT, source-spelled). **The cost of this choice falls on the 14B emitter.**
   Erasure is the hazard: the model must know that `List<String>` addresses as `List`, that
   `<T> void foo(T)` addresses as `foo(Object)` under erasure, that `int[]` may be `[I`, that
   `Object...` may be `Object[]`.

   **Recommendation: match on SOURCE SPELLING, not a canonical form.** The model has the file
   in context and is copying the parameter list it can see. Requiring it to canonicalise is a
   pure accuracy tax with no upside. This is not a hack — it is what JDT itself does for
   source elements (the `Q` unresolved signature form). Resolver rule: normalise whitespace,
   strip type arguments, compare token sequences; on ambiguity, fail loud.

3. **Anonymous / local class members — a whole category with no Python or Go analogue.**
   Python has no anonymous classes with methods. Go *cannot* declare a method on an anonymous
   type at all (a method needs a named receiver type). Java has methods living in
   `J.NewClass` bodies with no name anywhere in the language. **No string addresses them
   stably.** This is where the vocabulary genuinely does not survive.

4. **Field/method name collision — Java-only.** `int value;` and `int value()` can coexist in
   one Java class; a Go struct cannot have a field and method of the same name, and a Python
   attribute simply shadows. The address therefore needs a **kind discriminator**. Every
   scheme has one: Javadoc's parens, JDT's `^` vs `~`, SCIP's `.` vs `().`.

5. **Constructors need a distinguished name.** Python's `__init__` and Go's `NewX` are
   ordinary members. Java needs `<init>` / `<constructor>` / the class simple name.

6. **Records' compact constructor has no address in any existing scheme** (§3g).

## 6. RESOLVER RECOMMENDATION

**Primary: Eclipse JDT** (embeddable via `eclipse.jdt.ls` / `org.eclipse.jdt.core`).
- It is the only tool where the *plain node span already equals the replaceable unit*
  (Javadoc + annotations + body) — item 5 solved for free.
- `getExtendedStartPosition` handles trailing/non-Javadoc leading comments.
- It has a genuine round-trippable serialisable address (`getHandleIdentifier()` <->
  `JavaCore.create`) for **internal** use.
- Cost: JVM + workspace/`JavaCore` runtime in the harness. Heaviest option.
- **Do not expose handle identifiers to the model** — the format is explicitly unspecified,
  it is positional for anonymous types, and it demands `Q`-form signatures.

**Lightweight alternative: JavaParser.** Plain library, no workspace, no classpath needed
(and no classpath is a *feature* — the model's address is source-spelled anyway). You
implement resolution yourself by walking `TypeDeclaration` -> `CallableDeclaration` and
comparing normalised source-spelled parameter lists. You must assemble the extended span
yourself as `union(getComment().getRange(), getRange())`. Has the only dedicated
`CompactConstructorDeclaration` node, which is the only way to address §3g.

**Not recommended as the address format:**
- **SCIP/scip-java** — positional overload disambiguators (`+1`) that renumber under edit.
- **OpenRewrite** — the disqualifier is structural, not philosophical: the only
  declaration-matching entry point is
  `matches(J.MethodDeclaration, J.ClassDeclaration enclosing)`, and an anonymous class is a
  `J.NewClass` whose body is a `J.Block` — there is no `J.ClassDeclaration` in existence to
  pass. Anonymous-class methods are not "hard to match", they are **impossible to match**
  through this API. Secondarily, `MethodMatcher` is a *pattern* (zero, one, or many hits),
  not an address. OpenRewrite's real model is
  imperative visitor traversal (`Recipe` -> `TreeVisitor` -> `visitMethodDeclaration`), with
  `MethodMatcher` as a predicate inside the visit. It has **no serialisable single-element
  address**. Its losslessness is worth studying, but it is a transformation engine, not a
  resolver.

## 7. VERDICT FOR THE SCHEMA

```json
{"op": "replace_unit",
 "unit": "com.example.Outer.Inner#process(String,int)",
 "body": "..."}
```

Rules the harness must enforce:
- owner path dotted, inner classes with `.` (normalise `$` on input);
- `(...)` present => method/constructor; absent => field;
- `#<init>(...)` => constructor; `#<compact>()` => record compact constructor;
- **arity is the primary discriminator; type spelling is only a tiebreaker.** Match on
  parameter *count* first. If exactly one member of that name has that arity, resolve to it
  and **ignore the type spellings entirely**. Only compare normalised source-spelled types
  (type arguments stripped) when two or more same-name members share an arity.
  Rationale: the likeliest emitter error is a wrong type name with the right count — the
  model writes `foo(Object)` for `<T> void foo(T)`, or `String` where the file says
  `CharSequence`. Spelling-first matching turns that into either a spurious rejection or,
  worse, a *unique but wrong* match against a real sibling overload. Arity-first turns it
  into a correct resolution, and preserves fail-loud exactly where ambiguity is genuine.
- **resolution must be unique or the op fails loud** — never "first match wins";
- **members of anonymous classes, local classes and lambda bodies are REFUSED** — the model
  is told to emit whole-file for those. This is not a limitation to work around; it is the
  correct boundary, and the fallback already exists (E-D1).

So: the vocabulary **survives Java, but only with a signature and an explicit refusal
region.** The refusal region is new — Python and Go had none.
