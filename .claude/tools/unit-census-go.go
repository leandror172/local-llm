// Census of Go top-level declaration shapes, to test whether S3's
// symbol-addressed edit vocabulary survives the Go axis.
//
// Usage: go run gocensus.go <root> [<root>...]
package main

import (
	"fmt"
	"go/ast"
	"go/parser"
	"go/token"
	"os"
	"path/filepath"
	"sort"
	"strings"
)

type unit struct {
	name  string
	lines int
	file  string
}

type stats struct {
	files int
	lines int

	funcs, methods           int
	typeDecls, varDecls      int
	constDecls, importDecls  int
	groupedType, groupedVar  int
	groupedConst             int
	otherTop                 int

	namedLines int
	totalTop   int

	units       []unit // dotted-addressable
	topLevelMax map[string]int
	dottedMax   map[string]int
	fileLines   map[string]int

	structFieldBlocks []unit // type X struct{...} bodies
	ifaceBlocks       []unit
}

func recvType(fd *ast.FuncDecl) string {
	if fd.Recv == nil || len(fd.Recv.List) == 0 {
		return ""
	}
	switch t := fd.Recv.List[0].Type.(type) {
	case *ast.Ident:
		return t.Name
	case *ast.StarExpr:
		if id, ok := t.X.(*ast.Ident); ok {
			return id.Name
		}
		if idx, ok := t.X.(*ast.IndexExpr); ok { // generic receiver
			if id, ok := idx.X.(*ast.Ident); ok {
				return id.Name
			}
		}
	case *ast.IndexExpr:
		if id, ok := t.X.(*ast.Ident); ok {
			return id.Name
		}
	}
	return "?"
}

func main() {
	s := &stats{
		topLevelMax: map[string]int{},
		dottedMax:   map[string]int{},
		fileLines:   map[string]int{},
	}
	fset := token.NewFileSet()

	for _, root := range os.Args[1:] {
		filepath.Walk(root, func(path string, info os.FileInfo, err error) error {
			if err != nil || info.IsDir() {
				if err == nil && info.IsDir() {
					base := info.Name()
					if base == "vendor" || base == ".git" || base == "node_modules" {
						return filepath.SkipDir
					}
				}
				return nil
			}
			if !strings.HasSuffix(path, ".go") || strings.HasSuffix(path, "_test.go") {
				return nil
			}
			src, e := os.ReadFile(path)
			if e != nil {
				return nil
			}
			f, e := parser.ParseFile(fset, path, src, parser.ParseComments)
			if e != nil {
				return nil
			}
			s.files++
			nlines := len(strings.Split(string(src), "\n"))
			s.lines += nlines
			s.fileLines[path] = nlines

			span := func(n ast.Node) int {
				return fset.Position(n.End()).Line - fset.Position(n.Pos()).Line + 1
			}

			for _, d := range f.Decls {
				s.totalTop++
				switch decl := d.(type) {
				case *ast.FuncDecl:
					sp := span(decl)
					s.namedLines += sp
					name := decl.Name.Name
					if rt := recvType(decl); rt != "" {
						s.methods++
						name = rt + "." + name
					} else {
						s.funcs++
					}
					s.units = append(s.units, unit{name, sp, path})
					if sp > s.topLevelMax[path] {
						s.topLevelMax[path] = sp
					}
					if sp > s.dottedMax[path] {
						s.dottedMax[path] = sp
					}
				case *ast.GenDecl:
					sp := span(decl)
					grouped := decl.Lparen.IsValid()
					switch decl.Tok {
					case token.IMPORT:
						s.importDecls++
					case token.TYPE:
						s.typeDecls++
						s.namedLines += sp
						if grouped {
							s.groupedType++
						}
						if sp > s.topLevelMax[path] {
							s.topLevelMax[path] = sp
						}
						for _, spec := range decl.Specs {
							ts, ok := spec.(*ast.TypeSpec)
							if !ok {
								continue
							}
							ssp := span(ts)
							s.units = append(s.units, unit{ts.Name.Name, ssp, path})
							if ssp > s.dottedMax[path] {
								s.dottedMax[path] = ssp
							}
							switch bt := ts.Type.(type) {
							case *ast.StructType:
								s.structFieldBlocks = append(s.structFieldBlocks,
									unit{ts.Name.Name, span(bt), path})
							case *ast.InterfaceType:
								s.ifaceBlocks = append(s.ifaceBlocks,
									unit{ts.Name.Name, span(bt), path})
							}
						}
					case token.VAR, token.CONST:
						if decl.Tok == token.VAR {
							s.varDecls++
							if grouped {
								s.groupedVar++
							}
						} else {
							s.constDecls++
							if grouped {
								s.groupedConst++
							}
						}
						s.namedLines += sp
						if sp > s.topLevelMax[path] {
							s.topLevelMax[path] = sp
						}
						for _, spec := range decl.Specs {
							vs, ok := spec.(*ast.ValueSpec)
							if !ok || len(vs.Names) == 0 {
								continue
							}
							vsp := span(vs)
							s.units = append(s.units, unit{vs.Names[0].Name, vsp, path})
							if vsp > s.dottedMax[path] {
								s.dottedMax[path] = vsp
							}
						}
					}
				default:
					s.otherTop++
				}
			}
			return nil
		})
	}

	fmt.Printf("=== corpus: %d non-test .go files, %d lines ===\n\n", s.files, s.lines)
	fmt.Println("top-level declaration census:")
	fmt.Printf("  func (plain)      %5d\n", s.funcs)
	fmt.Printf("  func (method)     %5d   <- addressable only as Receiver.Method\n", s.methods)
	fmt.Printf("  type              %5d   (%d grouped in `type (...)`)\n", s.typeDecls, s.groupedType)
	fmt.Printf("  var               %5d   (%d grouped in `var (...)`)\n", s.varDecls, s.groupedVar)
	fmt.Printf("  const             %5d   (%d grouped in `const (...)`)\n", s.constDecls, s.groupedConst)
	fmt.Printf("  import            %5d\n", s.importDecls)
	fmt.Printf("  OTHER (unnamed)   %5d\n", s.otherTop)

	named := s.funcs + s.methods + s.typeDecls + s.varDecls + s.constDecls
	fmt.Printf("\n  named / total top-level: %d/%d = %.1f%%\n",
		named, s.totalTop, 100*float64(named)/float64(s.totalTop))
	fmt.Printf("  lines under a name:      %d/%d = %.1f%%\n",
		s.namedLines, s.lines, 100*float64(s.namedLines)/float64(s.lines))

	// ceilings
	var ratiosTop, ratiosDot []float64
	worstDot := unit{}
	for path, fl := range s.fileLines {
		if fl == 0 {
			continue
		}
		ratiosTop = append(ratiosTop, float64(s.topLevelMax[path])/float64(fl))
		r := float64(s.dottedMax[path]) / float64(fl)
		ratiosDot = append(ratiosDot, r)
		if s.dottedMax[path] > worstDot.lines {
			worstDot = unit{path, s.dottedMax[path], path}
		}
	}
	sort.Float64s(ratiosTop)
	sort.Float64s(ratiosDot)
	pct := func(v []float64, p float64) float64 {
		if len(v) == 0 {
			return 0
		}
		return v[int(p*float64(len(v)-1))] * 100
	}
	fmt.Printf("\n=== granularity ceiling (largest addressable unit as %% of its file) ===\n")
	fmt.Printf("  top-level addressing:  median %.0f%%  p90 %.0f%%  max %.0f%%\n",
		pct(ratiosTop, .5), pct(ratiosTop, .9), pct(ratiosTop, 1))
	fmt.Printf("  dotted addressing:     median %.0f%%  p90 %.0f%%  max %.0f%%\n",
		pct(ratiosDot, .5), pct(ratiosDot, .9), pct(ratiosDot, 1))

	sort.Slice(s.units, func(i, j int) bool { return s.units[i].lines > s.units[j].lines })
	fmt.Printf("\n  largest dotted units in corpus:\n")
	for i := 0; i < 6 && i < len(s.units); i++ {
		u := s.units[i]
		fmt.Printf("    %-42s %4d lines  (%s)\n", u.name, u.lines, filepath.Base(u.file))
	}
	if len(s.units) > 0 {
		mid := make([]int, len(s.units))
		for i, u := range s.units {
			mid[i] = u.lines
		}
		sort.Ints(mid)
		fmt.Printf("    median addressable unit: %d lines (n=%d)\n", mid[len(mid)/2], len(mid))
	}

	// struct/interface bodies — the Go analogue of "fields inside a class"
	big := 0
	for _, b := range s.structFieldBlocks {
		if b.lines > 30 {
			big++
		}
	}
	fmt.Printf("\n=== type bodies (the sub-unit question) ===\n")
	fmt.Printf("  struct types: %d  (%d with bodies >30 lines)\n", len(s.structFieldBlocks), big)
	fmt.Printf("  interface types: %d\n", len(s.ifaceBlocks))
	sort.Slice(s.structFieldBlocks, func(i, j int) bool {
		return s.structFieldBlocks[i].lines > s.structFieldBlocks[j].lines
	})
	for i := 0; i < 4 && i < len(s.structFieldBlocks); i++ {
		b := s.structFieldBlocks[i]
		fmt.Printf("    struct %-28s %4d lines (%s)\n", b.name, b.lines, filepath.Base(b.file))
	}
}
