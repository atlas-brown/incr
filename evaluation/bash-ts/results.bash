Testing bash
version: 5.1.16(1)-release
versinfo: 5 1 16 1 release x86_64-pc-linux-gnu
HOSTTYPE = x86_64
OSTYPE = linux-gnu
MACHTYPE = x86_64-pc-linux-gnu
Any output from any test, unless otherwise noted, indicates a possible anomaly
run-alias
50,51c50,51
< <aÃ¡ >
< foo
---
> <aÃ¡>
> bar
55,56c55,58
< foo c e x
< foo c file e x
---
> bar
> x
> bar
> x
62c64
< foo= bar=v
---
> foo=v bar=
run-appendop
run-arith
91,92c91,92
< ./arith.tests: line 177: let: jv += $iv: syntax error: operand expected (error token is "$iv")
< ./arith.tests: line 178: jv += $iv : syntax error: operand expected (error token is "$iv ")
---
> ./arith.tests: line 177: let: jv += $iv: arithmetic syntax error: operand expected (error token is "$iv")
> ./arith.tests: line 178: jv += $iv : arithmetic syntax error: operand expected (error token is "$iv ")
105c105
< ./arith.tests: line 207: 4 + : syntax error: operand expected (error token is "+ ")
---
> ./arith.tests: line 207: 4 + : arithmetic syntax error: operand expected (error token is "+ ")
140c140
< ./arith.tests: line 274: 7-- : syntax error: operand expected (error token is "- ")
---
> ./arith.tests: line 274: 7-- : arithmetic syntax error: operand expected (error token is "- ")
153,156c153,156
< ./arith1.sub: line 15: 4-- : syntax error: operand expected (error token is "- ")
< ./arith1.sub: line 16: 4++ : syntax error: operand expected (error token is "+ ")
< ./arith1.sub: line 17: 4 -- : syntax error: operand expected (error token is "- ")
< ./arith1.sub: line 18: 4 ++ : syntax error: operand expected (error token is "+ ")
---
> ./arith1.sub: line 15: 4-- : arithmetic syntax error: operand expected (error token is "- ")
> ./arith1.sub: line 16: 4++ : arithmetic syntax error: operand expected (error token is "+ ")
> ./arith1.sub: line 17: 4 -- : arithmetic syntax error: operand expected (error token is "- ")
> ./arith1.sub: line 18: 4 ++ : arithmetic syntax error: operand expected (error token is "+ ")
171c171
< ./arith1.sub: line 48: ((: ++ : syntax error: operand expected (error token is "+ ")
---
> ./arith1.sub: line 48: ((: ++ : arithmetic syntax error: operand expected (error token is "+ ")
174c174
< ./arith1.sub: line 51: ((: -- : syntax error: operand expected (error token is "- ")
---
> ./arith1.sub: line 51: ((: -- : arithmetic syntax error: operand expected (error token is "- ")
193c193
< ./arith2.sub: line 46: ((: -- : syntax error: operand expected (error token is "- ")
---
> ./arith2.sub: line 46: ((: -- : arithmetic syntax error: operand expected (error token is "- ")
196c196
< ./arith2.sub: line 50: ((: ++ : syntax error: operand expected (error token is "+ ")
---
> ./arith2.sub: line 50: ((: ++ : arithmetic syntax error: operand expected (error token is "+ ")
282c282
< ./arith9.sub: line 37: 4+: syntax error: operand expected (error token is "+")
---
> ./arith9.sub: line 37: 4+: arithmetic syntax error: operand expected (error token is "+")
291c291
< ./arith10.sub: line 33: " ": syntax error: operand expected (error token is "" "")
---
> ./arith10.sub: line 33: " ": arithmetic syntax error: operand expected (error token is "" "")
295c295
< ./arith10.sub: line 38: "": syntax error: operand expected (error token is """")
---
> ./arith10.sub: line 38: "": arithmetic syntax error: operand expected (error token is """")
311c311
< ./arith10.sub: line 33: " ": syntax error: operand expected (error token is "" "")
---
> ./arith10.sub: line 33: " ": arithmetic syntax error: operand expected (error token is "" "")
314,315c314,315
< declare -a a=([0]="18")
< ./arith10.sub: line 38: "": syntax error: operand expected (error token is """")
---
> ./arith10.sub: line 36: " ": arithmetic syntax error: operand expected (error token is "" "")
> ./arith10.sub: line 38: "": arithmetic syntax error: operand expected (error token is """")
318c318
< declare -a a=([0]="22")
---
> ./arith10.sub: line 41: "": arithmetic syntax error: operand expected (error token is """")
324c324
< declare -a a=([0]="26")
---
> ./arith10.sub: line 46: "": arithmetic syntax error: operand expected (error token is """")
340c340
< ./arith10.sub: line 80: "" : syntax error: operand expected (error token is """ ")
---
> ./arith10.sub: line 80: "" : arithmetic syntax error: operand expected (error token is """ ")
349c349
< ./arith10.sub: line 89: ((: 1 -  : syntax error: operand expected (error token is "-  ")
---
> ./arith10.sub: line 89: ((: 1 -  : arithmetic syntax error: operand expected (error token is "-  ")
354c354
< ./arith10.sub: line 94: let: 0 - "": syntax error: operand expected (error token is """")
---
> ./arith10.sub: line 94: let: 0 - "": arithmetic syntax error: operand expected (error token is """")
356c356
< ./arith10.sub: line 95: let: 0 - "": syntax error: operand expected (error token is """")
---
> ./arith10.sub: line 95: let: 0 - "": arithmetic syntax error: operand expected (error token is """")
359,361c359,361
< ./arith.tests: line 335: ((: x=9 y=41 : syntax error in expression (error token is "y=41 ")
< ./arith.tests: line 339: a b: syntax error in expression (error token is "b")
< ./arith.tests: line 340: ((: a b: syntax error in expression (error token is "b")
---
> ./arith.tests: line 335: ((: x=9 y=41 : arithmetic syntax error in expression (error token is "y=41 ")
> ./arith.tests: line 339: a b: arithmetic syntax error in expression (error token is "b")
> ./arith.tests: line 340: ((: a b: arithmetic syntax error in expression (error token is "b")
368,369c368,369
< ./arith.tests: line 351: syntax error near unexpected token `then'
< ./arith.tests: line 351: `if ((expr)) then ((expr)) fi'
---
> ./arith.tests: line 355: 'foo' : arithmetic syntax error: operand expected (error token is "'foo' ")
> ./arith.tests: line 358: b[c]d: arithmetic syntax error in expression (error token is "d")
run-arith-for
89c89
< ./arith-for.tests: line 133: ((: 7++ : syntax error: operand expected (error token is "+ ")
---
> ./arith-for.tests: line 133: ((: 7++ : arithmetic syntax error: operand expected (error token is "+ ")
93c93
< ./arith-for.tests: line 139: ((: j=: syntax error: operand expected (error token is "=")
---
> ./arith-for.tests: line 139: ((: j=: arithmetic syntax error: operand expected (error token is "=")
95,96c95,96
< ./arith-for.tests: line 145: syntax error near `;'
< ./arith-for.tests: line 145: `for (( $(case x in x) esac);; )); do break; done'
---
> ./arith-for.tests: line 141: break: only meaningful in a `for', `while', or `until' loop
> Y
run-array
58,59d57
< ./array.tests: line 133: [*]=last: cannot assign to non-numeric index
< ./array.tests: line 133: [-65]=negative: bad array subscript
71a70
> declare -a e=()
74c73
< ./array.tests: line 147: declare: c: cannot destroy array variables in this way
---
> ./array.tests: line 147: declare: c: readonly variable
88a88
> declare -a e=()
114,120c114,120
< ./array.tests: line 205: recho: command not found
< ./array.tests: line 206: recho: command not found
< ./array.tests: line 207: recho: command not found
< ./array.tests: line 208: recho: command not found
< ./array.tests: line 212: zecho: command not found
< ./array.tests: line 213: zecho: command not found
< ./array.tests: line 214: zecho: command not found
---
> argv[1] = <bin>
> argv[1] = </>
> argv[1] = <sbin>
> argv[1] = </>
> \bin \usr/bin \usr/ucb \usr/local/bin . \sbin \usr/sbin
> \bin \usr\bin \usr\ucb \usr\local\bin . \sbin \usr\sbin
> \bin \usr\bin \usr\ucb \usr\local\bin . \sbin \usr\sbin
126c126
< ./array.tests: line 238: -10]: bad array subscript
---
> ./array.tests: line 238: [-10]: bad array subscript
136c136
< ./array.tests: line 271: narray: unbound variable
---
> ./array.tests: line 271: narray[4]: unbound variable
175,178c175,187
< ./array.tests: line 343: recho: command not found
< ./array.tests: line 344: recho: command not found
< ./array.tests: line 345: recho: command not found
< ./array.tests: line 346: recho: command not found
---
> argv[1] = <0>
> argv[2] = <1>
> argv[3] = <4>
> argv[4] = <10>
> argv[1] = <0>
> argv[2] = <1>
> argv[3] = <4>
> argv[4] = <10>
> argv[1] = <0>
> argv[2] = <1>
> argv[3] = <4>
> argv[4] = <10>
> argv[1] = <0 1 4 10>
204a214
> FIN1:0
206c216,217
< FIN4:1
---
> FIN3:0
> FIN4:0
208c219
< FIN6:1
---
> FIN6:0
215c226,228
< ./array6.sub: line 22: recho: command not found
---
> argv[1] = <-iname 'a>
> argv[2] = <-iname 'b>
> argv[3] = <-iname 'c>
220,232c233,258
< ./array6.sub: line 33: recho: command not found
< ./array6.sub: line 40: recho: command not found
< ./array6.sub: line 41: recho: command not found
< ./array6.sub: line 44: recho: command not found
< ./array6.sub: line 45: recho: command not found
< ./array6.sub: line 56: recho: command not found
< ./array6.sub: line 59: recho: command not found
< ./array6.sub: line 62: recho: command not found
< ./array6.sub: line 65: recho: command not found
< ./array6.sub: line 68: recho: command not found
< ./array6.sub: line 73: recho: command not found
< ./array6.sub: line 76: recho: command not found
< ./array6.sub: line 79: recho: command not found
---
> argv[1] = <c>
> argv[2] = <d>
> argv[3] = <e>
> argv[4] = <f>
> argv[1] = <c d>
> argv[2] = <e f>
> argv[1] = <c d>
> argv[2] = <e f>
> argv[1] = <c d>
> argv[2] = <e f>
> argv[1] = <-iname 'abc>
> argv[2] = <-iname 'def>
> argv[1] = <-iname 'abc>
> argv[2] = <-iname 'def>
> argv[1] = <-iname>
> argv[2] = <abc -iname def>
> argv[1] = <-iname 'abc>
> argv[2] = <-iname 'def>
> argv[1] = <-iname>
> argv[2] = <abc -iname def>
> argv[1] = <-iname 'abc>
> argv[2] = <-iname 'def>
> argv[1] = <-iname 'abc>
> argv[2] = <-iname 'def>
> argv[1] = <-iname>
> argv[2] = <abc -iname def>
236,243c262,281
< ./array6.sub: line 108: recho: command not found
< ./array6.sub: line 109: recho: command not found
< ./array6.sub: line 111: recho: command not found
< ./array6.sub: line 112: recho: command not found
< ./array6.sub: line 115: recho: command not found
< ./array6.sub: line 116: recho: command not found
< ./array6.sub: line 118: recho: command not found
< ./array6.sub: line 119: recho: command not found
---
> argv[1] = <var with spaces>
> argv[1] = <var with spaces>
> argv[1] = <var with spacesab>
> argv[2] = <cd>
> argv[3] = <ef>
> argv[1] = <var with spacesab>
> argv[2] = <cd>
> argv[3] = <ef>
> argv[1] = <var with spacesab>
> argv[2] = <cd>
> argv[3] = <ef>
> argv[1] = <var with spacesab>
> argv[2] = <cd>
> argv[3] = <ef>
> argv[1] = <var with spacesab>
> argv[2] = <cd>
> argv[3] = <ef>
> argv[1] = <var with spacesab>
> argv[2] = <cd>
> argv[3] = <ef>
245,246c283,286
< ./array6.sub: line 124: recho: command not found
< ./array6.sub: line 125: recho: command not found
---
> argv[1] = <element1 with spaces>
> argv[2] = <element2 with spaces>
> argv[1] = <element1 with spaces>
> argv[2] = <element2 with spaces>
255,264c295,319
< ./array8.sub: line 21: recho: command not found
< ./array8.sub: line 22: recho: command not found
< ./array8.sub: line 24: recho: command not found
< ./array8.sub: line 25: recho: command not found
< ./array8.sub: line 27: recho: command not found
< ./array8.sub: line 28: recho: command not found
< ./array8.sub: line 31: recho: command not found
< ./array8.sub: line 32: recho: command not found
< ./array8.sub: line 34: recho: command not found
< ./array8.sub: line 35: recho: command not found
---
> argv[1] = <fooq//barq/>
> argv[1] = <fooq>
> argv[2] = <>
> argv[3] = <barq>
> argv[4] = <>
> argv[1] = <foo!//bar!/>
> argv[1] = <foo!>
> argv[2] = <>
> argv[3] = <bar!>
> argv[4] = <>
> argv[1] = <ooq//arq/>
> argv[1] = <ooq>
> argv[2] = <>
> argv[3] = <arq>
> argv[4] = <>
> argv[1] = <Fooq//Barq/>
> argv[1] = <Fooq>
> argv[2] = <>
> argv[3] = <Barq>
> argv[4] = <>
> argv[1] = <FOOQ//BARQ/>
> argv[1] = <FOOQ>
> argv[2] = <>
> argv[3] = <BARQ>
> argv[4] = <>
268,271c323,332
< ./array9.sub: line 19: recho: command not found
< ./array9.sub: line 23: recho: command not found
< ./array9.sub: line 30: recho: command not found
< ./array9.sub: line 39: recho: command not found
---
> argv[1] = <€>
> argv[1] = <~>
> argv[2] = <^?>
> argv[3] = <€>
> argv[1] = <~>
> argv[2] = <^?>
> argv[3] = <€>
> argv[1] = <~>
> argv[2] = <^?>
> argv[3] = <€>
337c398
< declare -a arr=([0]="0" [1]="0")
---
> declare -a arr=([0]="hello" [1]="world")
357c418
< ./array17.sub: line 43: ~: syntax error: operand expected (error token is "~")
---
> ./array17.sub: line 43: ~: arithmetic syntax error: operand expected (error token is "~")
372c433
< ./array17.sub: line 89: ~ : syntax error: operand expected (error token is "~ ")
---
> ./array17.sub: line 89: ~ : arithmetic syntax error: operand expected (error token is "~ ")
374,391c435,456
< ./array18.sub: line 19: recho: command not found
< ./array18.sub: line 21: recho: command not found
< ./array18.sub: line 22: recho: command not found
< ./array18.sub: line 23: recho: command not found
< ./array18.sub: line 24: recho: command not found
< ./array18.sub: line 27: recho: command not found
< ./array18.sub: line 28: recho: command not found
< ./array18.sub: line 29: recho: command not found
< ./array18.sub: line 30: recho: command not found
< ./array18.sub: line 36: recho: command not found
< ./array18.sub: line 38: recho: command not found
< ./array18.sub: line 39: recho: command not found
< ./array18.sub: line 40: recho: command not found
< ./array18.sub: line 41: recho: command not found
< ./array18.sub: line 44: recho: command not found
< ./array18.sub: line 45: recho: command not found
< ./array18.sub: line 46: recho: command not found
< ./array18.sub: line 47: recho: command not found
---
> argv[1] = <>
> argv[2] = <>
> argv[3] = <>
> argv[1] = <bar>
> argv[1] = <->
> argv[2] = <->
> argv[1] = <  >
> argv[1] = <qux>
> argv[1] = <->
> argv[2] = <->
> argv[1] = <  >
> argv[1] = <>
> argv[2] = <>
> argv[3] = <>
> argv[1] = <bar>
> argv[1] = <->
> argv[2] = <->
> argv[1] = <  >
> argv[1] = <qux>
> argv[1] = <->
> argv[2] = <->
> argv[1] = <  >
406c471
< ./array19.sub: line 89: total 0: syntax error in expression (error token is "0")
---
> ./array19.sub: line 89: total 0: arithmetic syntax error in expression (error token is "0")
440,441c505,506
< ./array20.sub: line 35: recho: command not found
< ./array20.sub: line 36: recho: command not found
---
> argv[1] = <a+b+c+d+e+f>
> argv[1] = <x+b+c+d+e+f>
449,450c514,515
< ./array21.sub: line 30: typeset: a: not found
< ./array21.sub: line 33: typeset: A: not found
---
> declare -a a=()
> declare -A A=([four]="4" [two]="2" [three]="3" [one]="1" )
455c520,521
< ./array22.sub: line 18: recho: command not found
---
> argv[1] = <>
> argv[2] = <>
457,458c523,524
< ./array22.sub: line 22: recho: command not found
< ./array22.sub: line 23: recho: command not found
---
> argv[1] = <y>
> argv[1] = <z>
460c526,527
< ./array22.sub: line 27: recho: command not found
---
> argv[1] = <>
> argv[2] = <x>
462c529
< ./array22.sub: line 31: recho: command not found
---
> argv[1] = <y>
464c531,532
< ./array22.sub: line 36: recho: command not found
---
> argv[1] = <>
> argv[2] = <>
466c534,535
< ./array22.sub: line 42: recho: command not found
---
> argv[1] = <>
> argv[2] = <x>
468c537
< ./array22.sub: line 48: recho: command not found
---
> argv[1] = <y>
471,480c540,547
< ./array23.sub: line 22: $( echo >&2 foo ) : syntax error: operand expected (error token is "$( echo >&2 foo ) ")
< ./array23.sub: line 23: $( echo >&2 foo ) : syntax error: operand expected (error token is "$( echo >&2 foo ) ")
< foo
< 0
< foo
< foo
< foo
< 6
< ./array23.sub: line 34: $( echo >&2 foo ): syntax error: operand expected (error token is "$( echo >&2 foo )")
< ./array23.sub: line 35: $( echo >&2 foo ): syntax error: operand expected (error token is "$( echo >&2 foo )")
---
> ./array23.sub: line 22: $( echo >&2 foo ) : arithmetic syntax error: operand expected (error token is "$( echo >&2 foo ) ")
> ./array23.sub: line 23: $( echo >&2 foo ) : arithmetic syntax error: operand expected (error token is "$( echo >&2 foo ) ")
> ./array23.sub: line 24: $( echo >&2 foo ) : arithmetic syntax error: operand expected (error token is "$( echo >&2 foo ) ")
> ./array23.sub: line 26: $( echo >&2 foo ) : arithmetic syntax error: operand expected (error token is "$( echo >&2 foo ) ")
> ./array23.sub: line 30: $( echo >&2 foo ): arithmetic syntax error: operand expected (error token is "$( echo >&2 foo )")
> ./array23.sub: line 33: $( echo >&2 foo ): arithmetic syntax error: operand expected (error token is "$( echo >&2 foo )")
> ./array23.sub: line 34: $index: arithmetic syntax error: operand expected (error token is "$index")
> ./array23.sub: line 35: $( echo >&2 foo ): arithmetic syntax error: operand expected (error token is "$( echo >&2 foo )")
534c601
< ./array25.sub: line 24: ' ': syntax error: operand expected (error token is "' '")
---
> ./array25.sub: line 24: ' ': arithmetic syntax error: operand expected (error token is "' '")
575,630c642,762
< ./array26.sub: line 20: recho: command not found
< ./array26.sub: line 21: recho: command not found
< ./array26.sub: line 23: recho: command not found
< ./array26.sub: line 24: recho: command not found
< ./array26.sub: line 27: recho: command not found
< ./array26.sub: line 28: recho: command not found
< ./array26.sub: line 29: recho: command not found
< ./array26.sub: line 30: recho: command not found
< ./array26.sub: line 34: recho: command not found
< ./array26.sub: line 35: recho: command not found
< ./array26.sub: line 36: recho: command not found
< ./array26.sub: line 37: recho: command not found
< ./array26.sub: line 39: recho: command not found
< ./array26.sub: line 40: recho: command not found
< ./array26.sub: line 41: recho: command not found
< ./array26.sub: line 42: recho: command not found
< ./array26.sub: line 47: recho: command not found
< ./array26.sub: line 54: recho: command not found
< ./array26.sub: line 55: recho: command not found
< ./array26.sub: line 56: recho: command not found
< ./array26.sub: line 57: recho: command not found
< ./array26.sub: line 62: recho: command not found
< ./array26.sub: line 63: recho: command not found
< ./array26.sub: line 64: recho: command not found
< ./array26.sub: line 65: recho: command not found
< ./array26.sub: line 67: recho: command not found
< ./array26.sub: line 68: recho: command not found
< ./array26.sub: line 69: recho: command not found
< ./array26.sub: line 70: recho: command not found
< ./array26.sub: line 75: recho: command not found
< ./array26.sub: line 82: recho: command not found
< ./array26.sub: line 83: recho: command not found
< ./array26.sub: line 84: recho: command not found
< ./array26.sub: line 85: recho: command not found
< ./array26.sub: line 91: recho: command not found
< ./array26.sub: line 92: recho: command not found
< ./array26.sub: line 93: recho: command not found
< ./array26.sub: line 94: recho: command not found
< ./array26.sub: line 97: recho: command not found
< ./array26.sub: line 98: recho: command not found
< ./array26.sub: line 99: recho: command not found
< ./array26.sub: line 100: recho: command not found
< ./array26.sub: line 101: recho: command not found
< ./array26.sub: line 108: recho: command not found
< ./array26.sub: line 109: recho: command not found
< ./array26.sub: line 110: recho: command not found
< ./array26.sub: line 111: recho: command not found
< ./array26.sub: line 115: recho: command not found
< ./array26.sub: line 116: recho: command not found
< ./array26.sub: line 119: recho: command not found
< ./array26.sub: line 120: recho: command not found
< ./array26.sub: line 121: recho: command not found
< ./array26.sub: line 128: recho: command not found
< ./array26.sub: line 129: recho: command not found
< ./array26.sub: line 130: recho: command not found
< ./array26.sub: line 131: recho: command not found
---
> argv[1] = <aa>
> argv[2] = <bb>
> argv[1] = <aa>
> argv[2] = <bb>
> argv[1] = <aa>
> argv[2] = <bb>
> argv[1] = <aa>
> argv[2] = <bb>
> argv[1] = <aa>
> argv[2] = <bb>
> argv[3] = <aa>
> argv[4] = <bb>
> argv[1] = <aa>
> argv[2] = <bb>
> argv[3] = <aa>
> argv[4] = <bb>
> argv[1] = <aa+bb>
> argv[2] = <aa+bb>
> argv[1] = <aa>
> argv[2] = <bb>
> argv[3] = <aa>
> argv[4] = <bb>
> argv[1] = <xa>
> argv[2] = <bb>
> argv[1] = <xa>
> argv[2] = <bb>
> argv[1] = <xa>
> argv[2] = <bb>
> argv[1] = <xa>
> argv[2] = <bb>
> argv[1] = <xa>
> argv[2] = <bb>
> argv[1] = <xa>
> argv[2] = <bb>
> argv[1] = <xa+bb>
> argv[1] = <xa+bb>
> argv[1] = <xa+bb>
> argv[2] = <xa+bb>
> argv[1] = <bb>
> argv[2] = <xa>
> argv[1] = <bb>
> argv[2] = <xa>
> argv[1] = <bb>
> argv[2] = <xa>
> argv[1] = <bb+xa>
> argv[1] = <xa>
> argv[2] = <bb>
> argv[1] = <xa>
> argv[2] = <bb>
> argv[1] = <xa>
> argv[2] = <bb>
> argv[1] = <xa>
> argv[2] = <bb>
> argv[1] = <xa>
> argv[2] = <bb>
> argv[1] = <xa>
> argv[2] = <bb>
> argv[1] = <xabb>
> argv[1] = <xabb>
> argv[1] = <xabb>
> argv[2] = <xabb>
> argv[1] = <bb>
> argv[2] = <xa>
> argv[1] = <bb>
> argv[2] = <xa>
> argv[1] = <bb>
> argv[2] = <xa>
> argv[1] = <bbxa>
> argv[1] = <aa>
> argv[2] = <bb>
> argv[1] = <aa>
> argv[2] = <bb>
> argv[1] = <aa>
> argv[2] = <bb>
> argv[1] = <aa>
> argv[2] = <bb>
> argv[1] = <aa>
> argv[2] = <bb>
> argv[3] = <aa>
> argv[4] = <bb>
> argv[1] = <aa>
> argv[2] = <bb>
> argv[3] = <aa>
> argv[4] = <bb>
> argv[1] = <aa+bb>
> argv[2] = <aa+bb>
> argv[1] = <aa+bb>
> argv[2] = <aa+bb>
> argv[1] = <aa>
> argv[2] = <bb>
> argv[3] = <aa>
> argv[4] = <bb>
> argv[1] = <bb>
> argv[2] = <aa>
> argv[1] = <bb>
> argv[2] = <aa>
> argv[1] = <bb>
> argv[2] = <aa>
> argv[1] = <bb+aa>
> argv[1] = <a>
> argv[2] = <b>
> argv[1] = <a>
> argv[2] = <b>
> argv[1] = <a>
> argv[2] = <b>
> argv[3] = <a>
> argv[4] = <b>
> argv[1] = <a+b>
> argv[2] = <a+b>
> argv[1] = <a>
> argv[2] = <b>
> argv[3] = <a>
> argv[4] = <b>
> argv[1] = <b>
> argv[2] = <a>
> argv[1] = <b>
> argv[2] = <a>
> argv[1] = <b>
> argv[2] = <a>
> argv[1] = <b+a>
> 7
632d763
< ./array27.sub: line 24: a[]]=7 : syntax error: invalid arithmetic operator (error token is "]=7 ")
634,635d764
< ./array27.sub: line 36: ((: A[]]=2 : syntax error: invalid arithmetic operator (error token is "]=2 ")
< declare -A A=([$'\t']="2" ["*"]="2" [" "]="2" ["@"]="2" )
637c766,767
< ./array27.sub: line 52: A[]]: bad array subscript
---
> declare -A A=([$'\t']="2" ["*"]="2" [" "]="2" ["]"]="2" ["@"]="2" )
> ./array27.sub: line 52: read: `A[]]': not a valid identifier
639c769
< ./array27.sub: line 60: A[]]: bad array subscript
---
> ./array27.sub: line 60: printf: `A[]]': not a valid identifier
644,646c774
< ./array27.sub: line 76: A[*]: bad array subscript
< ./array27.sub: line 76: A[@]: bad array subscript
< declare -A A
---
> declare -A A=(["*"]="X" ["@"]="X" )
658,662c786,790
< ./array29.sub: line 37: ${v2[@]@k}: bad substitution
< declare -a foo=([0]=$'\001\001')
< declare -a foo=([0]=$'\001\001')
< declare -A foo=([v]=$'\001\001' )
< declare -A foo=([v]=$'\001\001' )
---
> declare -A foo=([$'\001']=$'ab\001c' )
> declare -a foo=([0]=$'\001\001\001\001')
> declare -a foo=([0]=$'\001\001\001\001')
> declare -A foo=([v]=$'\001\001\001\001' )
> declare -A foo=([v]=$'\001\001\001\001' )
669c797
< 4+3
---
> 7
673c801
< foo
---
> FOO
675,676c803,804
< ./array30.sub: line 45: A[@]: bad array subscript
< declare -Au A=()
---
> FOO
> declare -Au A=(["@"]="FOO" )
683,684c811,815
< ./array32.sub: line 18: shopt: array_expand_once: invalid shell option name
< INJECTION!
---
> ./array32.sub: line 20: $(echo INJECTION! >&2 ; echo 0): arithmetic syntax error: operand expected (error token is "$(echo INJECTION! >&2 ; echo 0)")
> ./array32.sub: line 21: declare: a: not found
> ./array32.sub: line 24: $(echo INJECTION! >&2 ; echo 0): arithmetic syntax error: operand expected (error token is "$(echo INJECTION! >&2 ; echo 0)")
> ./array32.sub: line 25: declare: a: not found
> ./array32.sub: line 29: $(echo INJECTION! >&2 ; echo 0): arithmetic syntax error: operand expected (error token is "$(echo INJECTION! >&2 ; echo 0)")
686,689d816
< INJECTION!
< declare -a a=([0]="hi")
< INJECTION!
< declare -a a=()
691,714c818,839
< INJECTION!
< declare -a a=([0]="hi")
< INJECTION!
< declare -a a=([0]="hi")
< INJECTION!
< declare -a a=([0]="641129")
< INJECTION!
< declare -ai a=([0]="42")
< INJECTION!
< set
< INJECTION!
< set
< INJECTION!
< INJECTION!
< declare -a a=([0]="1")
< INJECTION!
< declare -a a=([0]="2")
< ./array32.sub: line 80: $(echo INJECTION! >&2 ; echo 0): syntax error: operand expected (error token is "$(echo INJECTION! >&2 ; echo 0)")
< declare -a a=([0]="2")
< ./array32.sub: line 85: $(echo INJECTION! >&2 ; echo 0): syntax error: operand expected (error token is "$(echo INJECTION! >&2 ; echo 0)")
< INJECTION!
< declare -a a=([0]="hi")
< INJECTION!
< declare -a a=([0]="hi")
---
> ./array32.sub: line 38: $(echo INJECTION! >&2 ; echo 0): arithmetic syntax error: operand expected (error token is "$(echo INJECTION! >&2 ; echo 0)")
> ./array32.sub: line 39: declare: a: not found
> ./array32.sub: line 42: $(echo INJECTION! >&2 ; echo 0): arithmetic syntax error: operand expected (error token is "$(echo INJECTION! >&2 ; echo 0)")
> declare -a a
> ./array32.sub: line 50: $(echo INJECTION! >&2 ; echo 0): arithmetic syntax error: operand expected (error token is "$(echo INJECTION! >&2 ; echo 0)")
> declare -a a
> ./array32.sub: line 57: $(echo INJECTION! >&2 ; echo 0): arithmetic syntax error: operand expected (error token is "$(echo INJECTION! >&2 ; echo 0)")
> declare -ai a
> ./array32.sub: line 65: $(echo INJECTION! >&2 ; echo 0): arithmetic syntax error: operand expected (error token is "$(echo INJECTION! >&2 ; echo 0)")
> ./array32.sub: line 66: $(echo INJECTION! >&2 ; echo 0): arithmetic syntax error: operand expected (error token is "$(echo INJECTION! >&2 ; echo 0)")
> ./array32.sub: line 68: $(echo INJECTION! >&2 ; echo 0): arithmetic syntax error: operand expected (error token is "$(echo INJECTION! >&2 ; echo 0)")
> ./array32.sub: line 75: $(echo INJECTION! >&2 ; echo 0): arithmetic syntax error: operand expected (error token is "$(echo INJECTION! >&2 ; echo 0)")
> declare -a a
> ./array32.sub: line 77: $(echo INJECTION! >&2 ; echo 0): arithmetic syntax error: operand expected (error token is "$(echo INJECTION! >&2 ; echo 0)")
> declare -a a
> ./array32.sub: line 80: $(echo INJECTION! >&2 ; echo 0): arithmetic syntax error: operand expected (error token is "$(echo INJECTION! >&2 ; echo 0)")
> declare -a a
> ./array32.sub: line 85: $(echo INJECTION! >&2 ; echo 0): arithmetic syntax error: operand expected (error token is "$(echo INJECTION! >&2 ; echo 0)")
> ./array32.sub: line 91: $(echo INJECTION! >&2 ; echo 0): arithmetic syntax error: operand expected (error token is "$(echo INJECTION! >&2 ; echo 0)")
> declare -a a=()
> ./array32.sub: line 95: $(echo INJECTION! >&2 ; echo 0): arithmetic syntax error: operand expected (error token is "$(echo INJECTION! >&2 ; echo 0)")
> declare -a a=()
716,718c841,845
< ./array33.sub: line 20: '1': syntax error: operand expected (error token is "'1'")
< declare -a A=()
< declare -a A=([1]="1")
---
> declare -A A=([1]="1" )
> ./array33.sub: line 27: f: A: cannot convert associative to indexed array
> ./array33.sub: line 27: declare: A: cannot convert associative to indexed array
> ./array33.sub: line 31: A: cannot convert associative to indexed array
> declare -A A=([1]="1" )
725c852
< ./array33.sub: line 52: read: A: cannot convert associative to indexed array
---
> ./array33.sub: line 52: read: A: not an indexed array
run-array2
1,56c1,74
< ./array-at-star: line 6: recho: command not found
< ./array-at-star: line 10: recho: command not found
< ./array-at-star: line 14: recho: command not found
< ./array-at-star: line 16: recho: command not found
< ./array-at-star: line 17: recho: command not found
< ./array-at-star: line 22: recho: command not found
< ./array-at-star: line 23: recho: command not found
< ./array-at-star: line 24: recho: command not found
< ./array-at-star: line 25: recho: command not found
< ./array-at-star: line 29: recho: command not found
< ./array-at-star: line 30: recho: command not found
< ./array-at-star: line 31: recho: command not found
< ./array-at-star: line 32: recho: command not found
< ./array-at-star: line 36: recho: command not found
< ./array-at-star: line 37: recho: command not found
< ./array-at-star: line 38: recho: command not found
< ./array-at-star: line 39: recho: command not found
< ./array-at-star: line 43: recho: command not found
< ./array-at-star: line 44: recho: command not found
< ./array-at-star: line 45: recho: command not found
< ./array-at-star: line 46: recho: command not found
< ./array-at-star: line 53: recho: command not found
< ./array-at-star: line 54: recho: command not found
< ./array-at-star: line 55: recho: command not found
< ./array-at-star: line 56: recho: command not found
< ./array-at-star: line 60: recho: command not found
< ./array-at-star: line 61: recho: command not found
< ./array-at-star: line 62: recho: command not found
< ./array-at-star: line 63: recho: command not found
< ./array-at-star: line 67: recho: command not found
< ./array-at-star: line 68: recho: command not found
< ./array-at-star: line 69: recho: command not found
< ./array-at-star: line 70: recho: command not found
< ./array-at-star: line 77: recho: command not found
< ./array-at-star: line 78: recho: command not found
< ./array-at-star: line 79: recho: command not found
< ./array-at-star: line 80: recho: command not found
< ./array-at-star: line 84: recho: command not found
< ./array-at-star: line 85: recho: command not found
< ./array-at-star: line 86: recho: command not found
< ./array-at-star: line 87: recho: command not found
< ./array-at-star: line 92: recho: command not found
< ./array-at-star: line 93: recho: command not found
< ./array-at-star: line 94: recho: command not found
< ./array-at-star: line 95: recho: command not found
< ./array-at-star: line 99: recho: command not found
< ./array-at-star: line 100: recho: command not found
< ./array-at-star: line 101: recho: command not found
< ./array-at-star: line 102: recho: command not found
< ./array-at-star: line 107: recho: command not found
< ./array-at-star: line 108: recho: command not found
< ./array-at-star: line 113: recho: command not found
< ./array-at-star: line 114: recho: command not found
< ./array-at-star: line 118: recho: command not found
< ./array-at-star: line 119: recho: command not found
< ./array-at-star: line 120: recho: command not found
---
> argv[1] = <a b>
> argv[1] = <ab>
> argv[1] = <a b>
> argv[1] = <a>
> argv[2] = <b>
> argv[1] = <a>
> argv[2] = <b>
> argv[1] = <3>
> argv[1] = <bob>
> argv[1] = <tom dick harry>
> argv[1] = <joe>
> argv[1] = <3>
> argv[1] = <bob>
> argv[1] = <tom dick harry>
> argv[1] = <joe>
> argv[1] = <3>
> argv[1] = <bob>
> argv[1] = <tom dick harry>
> argv[1] = <joe>
> argv[1] = <3>
> argv[1] = <bob>
> argv[1] = <tom dick harry>
> argv[1] = <joe>
> argv[1] = <1>
> argv[1] = <bobtom dick harryjoe>
> argv[1] = <3>
> argv[1] = <bob>
> argv[1] = <tom dick harry>
> argv[1] = <joe>
> argv[1] = <3>
> argv[1] = <bob>
> argv[1] = <tom dick harry>
> argv[1] = <joe>
> argv[1] = <5>
> argv[1] = <bob>
> argv[1] = <tom>
> argv[1] = <dick>
> argv[1] = <5>
> argv[1] = <bob>
> argv[1] = <tom>
> argv[1] = <dick>
> argv[1] = <1>
> argv[1] = <bob>
> argv[2] = <tom>
> argv[3] = <dick>
> argv[4] = <harry>
> argv[5] = <joe>
> argv[1] = <3>
> argv[1] = <bob>
> argv[1] = <tom>
> argv[2] = <dick>
> argv[3] = <harry>
> argv[1] = <joe>
> argv[1] = <a>
> argv[2] = <b>
> argv[3] = <c>
> argv[4] = <d>
> argv[5] = <e>
> argv[1] = <a>
> argv[2] = <b>
> argv[3] = <c>
> argv[4] = <d>
> argv[5] = <e>
> argv[1] = <foo>
> argv[2] = <bar>
> argv[3] = <bam>
> argv[1] = <foobarbam>
> argv[1] = <foo>
> argv[2] = <bar>
> argv[3] = <bam>
> argv[1] = <foo>
> argv[2] = <bar>
> argv[3] = <bam>
> argv[1] = <foo bar bam>
run-assoc
19,21c19
< ./assoc.tests: line 53: chaff[*]: bad array subscript
< ./assoc.tests: line 54: [*]=12: invalid associative array key
< declare -A chaff=(["hello world"]="flip" [one]="a" )
---
> declare -A chaff=(["*"]="12" ["hello world"]="flip" [one]="a" )
23,26c21,35
< ./assoc.tests: line 63: recho: command not found
< ./assoc.tests: line 64: recho: command not found
< ./assoc.tests: line 66: recho: command not found
< ./assoc.tests: line 67: recho: command not found
---
> argv[1] = <multiple>
> argv[2] = <words>
> argv[3] = <12>
> argv[4] = <flip>
> argv[5] = <a>
> argv[1] = <multiple words>
> argv[2] = <12>
> argv[3] = <flip>
> argv[4] = <a>
> argv[1] = <multiple>
> argv[2] = <words>
> argv[3] = <12>
> argv[4] = <flip>
> argv[5] = <a>
> argv[1] = <multiple words 12 flip a>
28,29d36
< ./assoc.tests: line 73: chaff[*]: bad array subscript
< ./assoc.tests: line 74: [*]=12: invalid associative array key
31,32c38,40
< ./assoc.tests: line 86: recho: command not found
< ./assoc.tests: line 87: recho: command not found
---
> argv[1] = <qux>
> argv[2] = <qix>
> argv[1] = <qux qix>
34,35c42,43
< ./assoc.tests: line 96: recho: command not found
< ./assoc.tests: line 99: $unset]: bad array subscript
---
> argv[1] = <2>
> ./assoc.tests: line 99: [$unset]: bad array subscript
37,44c45,58
< ./assoc.tests: line 103: recho: command not found
< ./assoc.tests: line 112: recho: command not found
< ./assoc.tests: line 113: recho: command not found
< ./assoc.tests: line 122: recho: command not found
< ./assoc.tests: line 123: recho: command not found
< ./assoc.tests: line 132: recho: command not found
< ./assoc.tests: line 142: recho: command not found
< ./assoc.tests: line 143: recho: command not found
---
> argv[1] = <7>
> argv[1] = <qux>
> argv[2] = <qix>
> argv[3] = <blat>
> argv[1] = <qux qix blat>
> argv[1] = <16>
> argv[1] = <16>
> argv[1] = <6>
> argv[2] = <flix>
> argv[1] = <six>
> argv[2] = <foo>
> argv[3] = <bar>
> argv[1] = <six>
> argv[2] = <foo bar>
51,54c65,68
< ./assoc.tests: line 159: recho: command not found
< ./assoc.tests: line 160: recho: command not found
< ./assoc.tests: line 161: recho: command not found
< ./assoc.tests: line 162: recho: command not found
---
> argv[1] = <bin>
> argv[1] = </>
> argv[1] = <sbin>
> argv[1] = </>
63,65c77,79
< ./assoc.tests: line 184: zecho: command not found
< ./assoc.tests: line 185: zecho: command not found
< ./assoc.tests: line 186: zecho: command not found
---
> \usr/local/bin \bin . \usr/bin \usr/ucb \usr/sbin \bin \sbin
> \usr\local\bin \bin . \usr\bin \usr\ucb \usr\sbin \bin \sbin
> \usr\local\bin \bin . \usr\bin \usr\ucb \usr\sbin \bin \sbin
79c93,95
< ./assoc2.sub: line 20: recho: command not found
---
> argv[1] = </usr/sbin/foo>
> argv[2] = </usr/local/bin/qux>
> argv[3] = <-l>
85c101,104
< ./assoc2.sub: line 28: recho: command not found
---
> argv[1] = <cd /blat ; echo $PWD>
> argv[2] = </usr/sbin/foo>
> argv[3] = </bin/bash --login -o posix>
> argv[4] = </usr/local/bin/qux -l>
90c109,111
< ./assoc3.sub: line 19: recho: command not found
---
> argv[1] = <inside:>
> argv[2] = <six>
> argv[3] = <foo quux>
92,101c113,137
< ./assoc4.sub: line 22: recho: command not found
< ./assoc4.sub: line 23: recho: command not found
< ./assoc4.sub: line 25: recho: command not found
< ./assoc4.sub: line 26: recho: command not found
< ./assoc4.sub: line 28: recho: command not found
< ./assoc4.sub: line 29: recho: command not found
< ./assoc4.sub: line 32: recho: command not found
< ./assoc4.sub: line 33: recho: command not found
< ./assoc4.sub: line 34: recho: command not found
< ./assoc4.sub: line 35: recho: command not found
---
> argv[1] = </barq//fooq>
> argv[1] = <>
> argv[2] = <barq>
> argv[3] = <>
> argv[4] = <fooq>
> argv[1] = </bar!//foo!>
> argv[1] = <>
> argv[2] = <bar!>
> argv[3] = <>
> argv[4] = <foo!>
> argv[1] = </arq//ooq>
> argv[1] = <>
> argv[2] = <arq>
> argv[3] = <>
> argv[4] = <ooq>
> argv[1] = </Barq//Fooq>
> argv[1] = <>
> argv[2] = <Barq>
> argv[3] = <>
> argv[4] = <Fooq>
> argv[1] = </BARQ//FOOQ>
> argv[1] = <>
> argv[2] = <BARQ>
> argv[3] = <>
> argv[4] = <FOOQ>
168,172c204
< ./assoc9.sub: line 36: unset: `dict[']': not a valid identifier
< ./assoc9.sub: line 36: unset: `dict["]': not a valid identifier
< ./assoc9.sub: line 36: unset: `dict[\]': not a valid identifier
< ./assoc9.sub: line 36: unset: `dict[`]': not a valid identifier
< declare -A dict=(["'"]="3" ["\""]="1" ["\\"]="4" ["\`"]="2" )
---
> declare -A dict=()
255,256c287
< ./assoc13.sub: line 31: a[@]: bad array subscript
< declare -A a
---
> declare -A a=(["@"]="at" )
259,266c290,292
< ./assoc13.sub: line 39: a[@]: bad array subscript
< declare -A a
< ./assoc13.sub: line 45: a[@]: bad array subscript
< declare -A a
< ./assoc13.sub: line 51: a[*]: bad array subscript
< ./assoc13.sub: line 52: a[@]: bad array subscript
< ./assoc13.sub: line 53: a[*]: bad array subscript
< declare -A a
---
> declare -A a=(["@"]="at2" )
> declare -A a=(["@"]="    string" )
> declare -A a=(["*"]="star2" ["@"]="at" )
268,274c294,331
< ./assoc14.sub: line 18: recho: command not found
< ./assoc14.sub: line 19: ${assoc[@]@k}: bad substitution
< ./assoc14.sub: line 21: recho: command not found
< ./assoc14.sub: line 22: ${assoc[*]@k}: bad substitution
< ./assoc14.sub: line 25: recho: command not found
< ./assoc14.sub: line 26: recho: command not found
< ./assoc14.sub: line 27: ${@@k}: bad substitution
---
> argv[1] = <world>
> argv[2] = <value with spaces>
> argv[3] = <bar>
> argv[4] = <1>
> argv[1] = <hello>
> argv[2] = <world>
> argv[3] = <key with spaces>
> argv[4] = <value with spaces>
> argv[5] = <foo>
> argv[6] = <bar>
> argv[7] = <one>
> argv[8] = <1>
> argv[1] = <world value with spaces bar 1>
> argv[1] = <hello world key with spaces value with spaces foo bar one 1>
> argv[1] = <hello>
> argv[2] = <world>
> argv[3] = <key with spaces>
> argv[4] = <value with spaces>
> argv[5] = <one>
> argv[6] = <1>
> argv[7] = <foo>
> argv[8] = <bar>
> argv[1] = <'hello'>
> argv[2] = <'world'>
> argv[3] = <'key with spaces'>
> argv[4] = <'value with spaces'>
> argv[5] = <'one'>
> argv[6] = <'1'>
> argv[7] = <'foo'>
> argv[8] = <'bar'>
> argv[1] = <'hello'>
> argv[2] = <'world'>
> argv[3] = <'key with spaces'>
> argv[4] = <'value with spaces'>
> argv[5] = <'one'>
> argv[6] = <'1'>
> argv[7] = <'foo'>
> argv[8] = <'bar'>
279,295c336,352
< ./assoc15.sub: line 25: ${var[@]@k}: bad substitution
< ./assoc15.sub: line 26: ${var[@]@k}: bad substitution
< declare -A foo
< declare -A var=([$'\001\001']=$'\001\001\001\001\001\001\001\001' )
< ./assoc15.sub: line 32: ${var[@]@k}: bad substitution
< ./assoc15.sub: line 33: ${var[@]@k}: bad substitution
< declare -A foo
< declare -A var=([$'\001\001']=$'\001\001\001\001\001\001\001\001' )
< ./assoc15.sub: line 39: ${var[@]@k}: bad substitution
< ./assoc15.sub: line 40: ${var[@]@k}: bad substitution
< declare -A foo
< declare -a var=([0]=$'\001\001\001\001\001\001\001\001')
< ./assoc15.sub: line 51: recho: command not found
< declare -a foo=([0]=$'\001\001\001\001\001\001\001\001')
< declare -a var=([0]=$'\001\001\001\001\001\001\001\001')
< ./assoc15.sub: line 61: recho: command not found
< declare -a foo=([0]=$'\001\001\001\001\001\001\001\001')
---
> argv[1] = <^A>
> argv[2] = <^A^A^A^A>
> declare -A foo=([$'\001']=$'\001\001\001\001' )
> declare -A var=([$'\001']=$'\001\001\001\001' )
> argv[1] = <^A>
> argv[2] = <^A^A^A^A>
> declare -A foo=([$'\001']=$'\001\001\001\001' )
> declare -A var=([$'\001']=$'\001\001\001\001' )
> argv[1] = <^A>
> argv[2] = <^A^A^A^A>
> declare -A foo=([$'\001']=$'\001\001\001\001' )
> declare -a var=([0]=$'\001\001\001\001')
> argv[1] = <$'\001\001\001\001'>
> declare -a foo=([0]=$'\001\001\001\001')
> declare -a var=([0]=$'\001\001\001\001')
> argv[1] = <$'\001\001\001\001'>
> declare -a foo=([0]=$'\001\001\001\001')
297c354
< ./assoc15.sub: line 75: ${var[@]@k}: bad substitution
---
> declare -A foo=([two]=$'ab\001cd' [one]=$'\001\001\001\001' )
299c356
< declare -A foo=([$'\001']=$'\001\001' )
---
> declare -A foo=([$'\001']=$'\001\001\001\001' )
302d358
< stderr
306d361
< stderr
310d364
< stderr
314d367
< stderr
318d370
< stderr
336a389
> declare -A A=()
337a391
> declare -A A=()
338a393
> declare -A A=()
339a395
> declare -A A=()
340a397
> declare -A A=()
342,347d398
< declare -A A=(["]"]="rbracket" ["["]="lbracket" )
< declare -A A=(["]"]="rbracket" ["["]="lbracket" )
< declare -A A=(["]"]="rbracket" ["["]="lbracket" )
< declare -A A=(["]"]="rbracket" ["["]="lbracket" )
< ./assoc18.sub: line 27: A[]]: bad array subscript
< declare -A A=(["["]="lbracket" )
349,350c400
< ./assoc18.sub: line 38: A[]]: bad array subscript
< declare -A A=(["["]="lbracket" )
---
> declare -A A=(["]"]="rbracket" ["["]="lbracket" )
352,353c402
< ./assoc18.sub: line 53: wait: `A[]]': not a valid identifier
< bad 1
---
> 5: ok 1
run-attr
2c2
< ./attr.tests: line 17: a: readonly variable
---
> ./attr.tests: line 17: f2: a: readonly variable
20c20
< ./attr1.sub: line 40: r: readonly variable
---
> ./attr1.sub: line 40: f: r: readonly variable
run-braces
18,21c18,19
< ./braces.tests: line 36: zecho: command not found
< 
< ./braces.tests: line 37: zecho: command not found
< 
---
> foo 1 2 bar
> foo 1 2 bar
27,34c25,28
< ./braces.tests: command substitution: line 56: unexpected EOF while looking for matching `"'
< ./braces.tests: command substitution: line 57: syntax error: unexpected end of file
< ./braces.tests: command substitution: line 57: unexpected EOF while looking for matching `"'
< ./braces.tests: command substitution: line 58: syntax error: unexpected end of file
< ./braces.tests: command substitution: line 58: unexpected EOF while looking for matching `"'
< ./braces.tests: command substitution: line 59: syntax error: unexpected end of file
< ./braces.tests: command substitution: line 60: unexpected EOF while looking for matching `"'
< ./braces.tests: command substitution: line 61: syntax error: unexpected end of file
---
> 4
> 4
> ./braces.tests: command substitution: line 59: unexpected EOF while looking for matching `)'
> 4
77,82c71,76
< 1..7 1..8 1..9 2..7 2..8 2..9 3..7 3..8 3..9
< {{a..c}..{1..3}}
< a..1 a..10 b..1 b..10 c..1 c..10
< a..1 a..2 a..3 a..4 c..1 c..2 c..3 c..4
< 1..4 2..4 3..4
< 6..7 6..8 6..9
---
> {1..7} {1..8} {1..9} {2..7} {2..8} {2..9} {3..7} {3..8} {3..9}
> {a..1} {a..2} {a..3} {b..1} {b..2} {b..3} {c..1} {c..2} {c..3}
> {a..1} {a..10} {b..1} {b..10} {c..1} {c..10}
> {a..1} {a..2} {a..3} {a..4} {c..1} {c..2} {c..3} {c..4}
> {1..4} {2..4} {3..4}
> {6..7} {6..8} {6..9}
run-builtins
129c129
< ./source7.sub: /tmp/x29-641424: bash: bad interpreter: No such file or directory
---
> one.1 subshell
132,133c132,133
< ./source7.sub: /tmp/x29-641424: bash: bad interpreter: No such file or directory
< ./source7.sub: /tmp/x29-641424: bash: bad interpreter: No such file or directory
---
> four.1 subshell
> one.2 subshell
136c136
< ./source7.sub: /tmp/x29-641424: bash: bad interpreter: No such file or directory
---
> four.2 subshell
144,151c144,147
< ./source8.sub: line 44: .: -p: invalid option
< .: usage: . filename [arguments]
< ./source8.sub: line 45: source: -p: invalid option
< source: usage: source filename [arguments]
< ./source8.sub: line 49: .: -p: invalid option
< .: usage: . filename [arguments]
< ./source8.sub: line 50: source: -p: invalid option
< source: usage: source filename [arguments]
---
> an improbable filename
> an improbable filename
> an improbable filename
> an improbable filename
153,156c149,151
< ./source8.sub: line 55: .: -p: invalid option
< .: usage: . filename [arguments]
< ./source8.sub: line 58: source: -p: invalid option
< source: usage: source filename [arguments]
---
> ./source8.sub: line 55: .: cwd-filename: file not found
> file in the current directory
> bash: line 1: .: cwd-filename: file not found
158,163c153,154
< bash: line 1: .: -p: invalid option
< .: usage: . filename [arguments]
< ./source8.sub: line 65: .: -p: invalid option
< .: usage: . filename [arguments]
< ./source8.sub: line 66: source: -p: invalid option
< source: usage: source filename [arguments]
---
> file in the current directory
> file in the current directory
212c203
< assoc A
---
> assoc A unset
223c214
< ./builtins5.sub: line 69: recho: command not found
---
> argv[1] = <one two three>
284,287c275,278
< ./builtins7.sub: line 14: recho: command not found
< 127
< ./builtins7.sub: line 15: recho: command not found
< 127
---
> argv[1] = <one>
> 0
> argv[1] = <two>
> 0
309,322c300,306
< ./builtins8.sub: line 16: umask: `+': invalid symbolic mode character
< u=rwx,g=rx,o=rx
< ./builtins8.sub: line 20: umask: `-': invalid symbolic mode character
< u=rwx,g=rx,o=rx
< ./builtins8.sub: line 24: umask: `u': invalid symbolic mode character
< u=rwx,g=rx,o=rx
< ./builtins8.sub: line 28: umask: `+': invalid symbolic mode character
< u=rwx,g=rx,o=rx
< ./builtins8.sub: line 32: umask: `=': invalid symbolic mode character
< u=rwx,g=rx,o=rx
< ./builtins8.sub: line 36: umask: `u': invalid symbolic mode character
< u=rwx,g=rx,o=rx
< ./builtins8.sub: line 40: umask: `u': invalid symbolic mode character
< u=rwx,g=rx,o=rx
---
> u=rw,g=rx,o=rx
> u=r,g=rx,o=rx
> u=rwx,g=rwx,o=
> u=rw,g=wx,o=rx
> u=rx,g=rx,o=rx
> u=rwx,g=rx,o=rwx
> u=rwx,g=rwx,o=rx
329d312
< ./builtins8.sub: line 68: umask: `X': invalid symbolic mode character
331d313
< ./builtins8.sub: line 72: umask: `X': invalid symbolic mode character
333d314
< ./builtins8.sub: line 76: umask: `X': invalid symbolic mode character
336,337c317
< ./builtins8.sub: line 84: umask: `g': invalid symbolic mode character
< u=rwx,g=rx,o=rx
---
> u=rwx,g=rx,o=x
339c319,320
< 0
---
> ./builtins9.sub: line 19: hash: notthere: not found
> 1
364,401c345,383
<  job_spec [&]                            history [-c] [-d offset] [n] or hist>
<  (( expression ))                        if COMMANDS; then COMMANDS; [ elif C>
<  . filename [arguments]                  jobs [-lnprs] [jobspec ...] or jobs >
<  :                                       kill [-s sigspec | -n signum | -sigs>
<  [ arg... ]                              let arg [arg ...]
<  [[ expression ]]                        local [option] name[=value] ...
<  alias [-p] [name[=value] ... ]          logout [n]
<  bg [job_spec ...]                       mapfile [-d delim] [-n count] [-O or>
<  bind [-lpsvPSVX] [-m keymap] [-f file>  popd [-n] [+N | -N]
<  break [n]                               printf [-v var] format [arguments]
<  builtin [shell-builtin [arg ...]]       pushd [-n] [+N | -N | dir]
<  caller [expr]                           pwd [-LP]
<  case WORD in [PATTERN [| PATTERN]...)>  read [-ers] [-a array] [-d delim] [->
<  cd [-L|[-P [-e]] [-@]] [dir]            readarray [-d delim] [-n count] [-O >
<  command [-pVv] command [arg ...]        readonly [-aAf] [name[=value] ...] o>
<  compgen [-abcdefgjksuv] [-o option] [>  return [n]
<  complete [-abcdefgjksuv] [-pr] [-DEI]>  select NAME [in WORDS ... ;] do COMM>
<  compopt [-o|+o option] [-DEI] [name .>  set [-abefhkmnptuvxBCHP] [-o option->
<  continue [n]                            shift [n]
<  coproc [NAME] command [redirections]    shopt [-pqsu] [-o] [optname ...]
<  declare [-aAfFgiIlnrtux] [-p] [name[=>  source filename [arguments]
<  dirs [-clpv] [+N] [-N]                  suspend [-f]
<  disown [-h] [-ar] [jobspec ... | pid >  test [expr]
<  echo [-neE] [arg ...]                   time [-p] pipeline
<  enable [-a] [-dnps] [-f filename] [na>  times
<  eval [arg ...]                          trap [-lp] [[arg] signal_spec ...]
<  exec [-cl] [-a name] [command [argume>  true
<  exit [n]                                type [-afptP] name [name ...]
<  export [-fn] [name[=value] ...] or ex>  typeset [-aAfFgiIlnrtux] [-p] name[=>
<  false                                   ulimit [-SHabcdefiklmnpqrstuvxPT] [l>
<  fc [-e ename] [-lnr] [first] [last] o>  umask [-p] [-S] [mode]
<  fg [job_spec]                           unalias [-a] name [name ...]
<  for NAME [in WORDS ... ] ; do COMMAND>  unset [-f] [-v] [-n] [name ...]
<  for (( exp1; exp2; exp3 )); do COMMAN>  until COMMANDS; do COMMANDS; done
<  function name { COMMANDS ; } or name >  variables - Names and meanings of so>
<  getopts optstring name [arg ...]        wait [-fn] [-p var] [id ...]
<  hash [-lr] [-p pathname] [-dt] [name >  while COMMANDS; do COMMANDS; done
<  help [-dms] [pattern ...]               { COMMANDS ; }
---
>  ! PIPELINE                              history [-c] [-d offset] [n] or hist>
>  job_spec [&]                            if COMMANDS; then COMMANDS; [ elif C>
>  (( expression ))                        jobs [-lnprs] [jobspec ...] or jobs >
>  . [-p path] filename [arguments]        kill [-s sigspec | -n signum | -sigs>
>  :                                       let arg [arg ...]
>  [ arg... ]                              local [option] name[=value] ...
>  [[ expression ]]                        logout [n]
>  alias [-p] [name[=value] ... ]          mapfile [-d delim] [-n count] [-O or>
>  bg [job_spec ...]                       popd [-n] [+N | -N]
>  bind [-lpsvPSVX] [-m keymap] [-f file>  printf [-v var] format [arguments]
>  break [n]                               pushd [-n] [+N | -N | dir]
>  builtin [shell-builtin [arg ...]]       pwd [-LP]
>  caller [expr]                           read [-Eers] [-a array] [-d delim] [>
>  case WORD in [PATTERN [| PATTERN]...)>  readarray [-d delim] [-n count] [-O >
>  cd [-L|[-P [-e]]] [-@] [dir]            readonly [-aAf] [name[=value] ...] o>
>  command [-pVv] command [arg ...]        return [n]
>  compgen [-V varname] [-abcdefgjksuv] >  select NAME [in WORDS ... ;] do COMM>
>  complete [-abcdefgjksuv] [-pr] [-DEI]>  set [-abefhkmnptuvxBCEHPT] [-o optio>
>  compopt [-o|+o option] [-DEI] [name .>  shift [n]
>  continue [n]                            shopt [-pqsu] [-o] [optname ...]
>  coproc [NAME] command [redirections]    source [-p path] filename [argument>
>  declare [-aAfFgiIlnrtux] [name[=value>  suspend [-f]
>  dirs [-clpv] [+N] [-N]                  test [expr]
>  disown [-h] [-ar] [jobspec ... | pid >  time [-p] pipeline
>  echo [-neE] [arg ...]                   times
>  enable [-a] [-dnps] [-f filename] [na>  trap [-Plp] [[action] signal_spec ..>
>  eval [arg ...]                          true
>  exec [-cl] [-a name] [command [argume>  type [-afptP] name [name ...]
>  exit [n]                                typeset [-aAfFgiIlnrtux] name[=value>
>  export [-fn] [name[=value] ...] or ex>  ulimit [-SHabcdefiklmnpqrstuvxPRT] [>
>  false                                   umask [-p] [-S] [mode]
>  fc [-e ename] [-lnr] [first] [last] o>  unalias [-a] name [name ...]
>  fg [job_spec]                           unset [-f] [-v] [-n] [name ...]
>  for NAME [in WORDS ... ] ; do COMMAND>  until COMMANDS; do COMMANDS-2; done
>  for (( exp1; exp2; exp3 )); do COMMAN>  variables - Names and meanings of so>
>  function name { COMMANDS ; } or name >  wait [-fn] [-p var] [id ...]
>  getopts optstring name [arg ...]        while COMMANDS; do COMMANDS-2; done
>  hash [-lr] [-p pathname] [-dt] [name >  { COMMANDS ; }
>  help [-dms] [pattern ...]
416c398
< read: read [-ers] [-a array] [-d delim] [-i text] [-n nchars] [-N nchars] [-p prompt] [-t timeout] [-u fd] [name ...]
---
> read: read [-Eers] [-a array] [-d delim] [-i text] [-n nchars] [-N nchars] [-p prompt] [-t timeout] [-u fd] [name ...]
419c401
< read: read [-ers] [-a array] [-d delim] [-i text] [-n nchars] [-N nchars] [-p prompt] [-t timeout] [-u fd] [name ...]
---
> read: read [-Eers] [-a array] [-d delim] [-i text] [-n nchars] [-N nchars] [-p prompt] [-t timeout] [-u fd] [name ...]
447c429
<     Copyright (C) 2020 Free Software Foundation, Inc.
---
>     Copyright (C) 2025 Free Software Foundation, Inc.
456,493c438,476
<  job_spec [&]                            history [-c] [-d offset] [n] or hist>
<  (( expression ))                        if COMMANDS; then COMMANDS; [ elif C>
<  . filename [arguments]                  jobs [-lnprs] [jobspec ...] or jobs >
<  :                                       kill [-s sigspec | -n signum | -sigs>
<  [ arg... ]                              let arg [arg ...]
<  [[ expression ]]                        local [option] name[=value] ...
<  alias [-p] [name[=value] ... ]          logout [n]
<  bg [job_spec ...]                       mapfile [-d delim] [-n count] [-O or>
<  bind [-lpsvPSVX] [-m keymap] [-f file>  popd [-n] [+N | -N]
<  break [n]                               printf [-v var] format [arguments]
<  builtin [shell-builtin [arg ...]]       pushd [-n] [+N | -N | dir]
<  caller [expr]                           pwd [-LP]
<  case WORD in [PATTERN [| PATTERN]...)>  read [-ers] [-a array] [-d delim] [->
<  cd [-L|[-P [-e]] [-@]] [dir]            readarray [-d delim] [-n count] [-O >
<  command [-pVv] command [arg ...]        readonly [-aAf] [name[=value] ...] o>
<  compgen [-abcdefgjksuv] [-o option] [>  return [n]
<  complete [-abcdefgjksuv] [-pr] [-DEI]>  select NAME [in WORDS ... ;] do COMM>
<  compopt [-o|+o option] [-DEI] [name .>  set [-abefhkmnptuvxBCHP] [-o option->
<  continue [n]                            shift [n]
<  coproc [NAME] command [redirections]    shopt [-pqsu] [-o] [optname ...]
<  declare [-aAfFgiIlnrtux] [-p] [name[=>  source filename [arguments]
<  dirs [-clpv] [+N] [-N]                  suspend [-f]
<  disown [-h] [-ar] [jobspec ... | pid >  test [expr]
<  echo [-neE] [arg ...]                   time [-p] pipeline
<  enable [-a] [-dnps] [-f filename] [na>  times
<  eval [arg ...]                          trap [-lp] [[arg] signal_spec ...]
<  exec [-cl] [-a name] [command [argume>  true
<  exit [n]                                type [-afptP] name [name ...]
<  export [-fn] [name[=value] ...] or ex>  typeset [-aAfFgiIlnrtux] [-p] name[=>
<  false                                   ulimit [-SHabcdefiklmnpqrstuvxPT] [l>
<  fc [-e ename] [-lnr] [first] [last] o>  umask [-p] [-S] [mode]
<  fg [job_spec]                           unalias [-a] name [name ...]
<  for NAME [in WORDS ... ] ; do COMMAND>  unset [-f] [-v] [-n] [name ...]
<  for (( exp1; exp2; exp3 )); do COMMAN>  until COMMANDS; do COMMANDS; done
<  function name { COMMANDS ; } or name >  variables - Names and meanings of so>
<  getopts optstring name [arg ...]        wait [-fn] [-p var] [id ...]
<  hash [-lr] [-p pathname] [-dt] [name >  while COMMANDS; do COMMANDS; done
<  help [-dms] [pattern ...]               { COMMANDS ; }
---
>  ! PIPELINE                              history [-c] [-d offset] [n] or hist>
>  job_spec [&]                            if COMMANDS; then COMMANDS; [ elif C>
>  (( expression ))                        jobs [-lnprs] [jobspec ...] or jobs >
>  . [-p path] filename [arguments]        kill [-s sigspec | -n signum | -sigs>
>  :                                       let arg [arg ...]
>  [ arg... ]                              local [option] name[=value] ...
>  [[ expression ]]                        logout [n]
>  alias [-p] [name[=value] ... ]          mapfile [-d delim] [-n count] [-O or>
>  bg [job_spec ...]                       popd [-n] [+N | -N]
>  bind [-lpsvPSVX] [-m keymap] [-f file>  printf [-v var] format [arguments]
>  break [n]                               pushd [-n] [+N | -N | dir]
>  builtin [shell-builtin [arg ...]]       pwd [-LP]
>  caller [expr]                           read [-Eers] [-a array] [-d delim] [>
>  case WORD in [PATTERN [| PATTERN]...)>  readarray [-d delim] [-n count] [-O >
>  cd [-L|[-P [-e]]] [-@] [dir]            readonly [-aAf] [name[=value] ...] o>
>  command [-pVv] command [arg ...]        return [n]
>  compgen [-V varname] [-abcdefgjksuv] >  select NAME [in WORDS ... ;] do COMM>
>  complete [-abcdefgjksuv] [-pr] [-DEI]>  set [-abefhkmnptuvxBCEHPT] [-o optio>
>  compopt [-o|+o option] [-DEI] [name .>  shift [n]
>  continue [n]                            shopt [-pqsu] [-o] [optname ...]
>  coproc [NAME] command [redirections]    source [-p path] filename [argument>
>  declare [-aAfFgiIlnrtux] [name[=value>  suspend [-f]
>  dirs [-clpv] [+N] [-N]                  test [expr]
>  disown [-h] [-ar] [jobspec ... | pid >  time [-p] pipeline
>  echo [-neE] [arg ...]                   times
>  enable [-a] [-dnps] [-f filename] [na>  trap [-Plp] [[action] signal_spec ..>
>  eval [arg ...]                          true
>  exec [-cl] [-a name] [command [argume>  type [-afptP] name [name ...]
>  exit [n]                                typeset [-aAfFgiIlnrtux] name[=value>
>  export [-fn] [name[=value] ...] or ex>  ulimit [-SHabcdefiklmnpqrstuvxPRT] [>
>  false                                   umask [-p] [-S] [mode]
>  fc [-e ename] [-lnr] [first] [last] o>  unalias [-a] name [name ...]
>  fg [job_spec]                           unset [-f] [-v] [-n] [name ...]
>  for NAME [in WORDS ... ] ; do COMMAND>  until COMMANDS; do COMMANDS-2; done
>  for (( exp1; exp2; exp3 )); do COMMAN>  variables - Names and meanings of so>
>  function name { COMMANDS ; } or name >  wait [-fn] [-p var] [id ...]
>  getopts optstring name [arg ...]        while COMMANDS; do COMMANDS-2; done
>  hash [-lr] [-p pathname] [-dt] [name >  { COMMANDS ; }
>  help [-dms] [pattern ...]
496,498d478
< ./builtins11.sub: line 20: ${ ulimit -c; }: bad substitution
< unlimited
< unlimited
499a480
> ./builtins11.sub: line 27: ulimit: +1999: invalid number
503c484
< ulimit: usage: ulimit [-SHabcdefiklmnpqrstuvxPT] [limit]
---
> ulimit: usage: ulimit [-SHabcdefiklmnpqrstuvxPRT] [limit]
524a506
> after non-numeric arg to exit: 2
run-case
17,18c17,66
< ./case.tests: line 66: syntax error near unexpected token `esac'
< ./case.tests: line 66: `case esac in (esac) echo esac;; esac'
---
> esac
> unset word ok 1
> unset word ok 2
> unset word ok 3
> ok 1
> ok 2
> ok 3
> ok 4
> ok 5
> ok 6
> ok 7
> ok 8
> ok 9
> mysterious 1
> mysterious 2
> argv[1] = <\a\b\c\^A\d\e\f>
> argv[1] = <\a\b\c\^A\d\e\f>
> argv[1] = <abc^Adef>
> ok 1
> ok 2
> ok 3
> ok 4
> ok 5
> ok 6
> ok 7
> ok 8
> --- testing: soh
> ok1ok2ok3ok4ok5
> ok1ok2ok3ok4ok5
> ok1ok2ok3ok4ok5
> ok1ok2ok3ok4ok5
> ok1ok2ok3ok4ok5
> ok1ok2ok3ok4ok5
> ok1ok2ok3ok4ok5
> --- testing: stx
> ok1ok2ok3ok4ok5
> ok1ok2ok3ok4ok5
> ok1ok2ok3ok4ok5
> ok1ok2ok3ok4ok5
> ok1ok2ok3ok4ok5
> ok1ok2ok3ok4ok5
> ok1ok2ok3ok4ok5
> --- testing: del
> ok1ok2ok3ok4ok5
> ok1ok2ok3ok4ok5
> ok1ok2ok3ok4ok5
> ok1ok2ok3ok4ok5
> ok1ok2ok3ok4ok5
> ok1ok2ok3ok4ok5
> ok1ok2ok3ok4ok5
run-casemod
run-complete
2d1
< complete -c nice
4d2
< complete -c gdb
6d3
< complete -j -P '%' fg
8,9d4
< complete -f -X '!*.dvi' dvips
< complete -f -X '!*.texi*' texi2dvi
11d5
< complete -f .
16,17d9
< complete -v -S '=' declare
< complete -v -S '=' export
21d12
< complete -f -X '!*.dvi' xdvi
26d16
< complete -u su
28,29d17
< complete -o dirnames -o filenames -o nospace -d popd
< complete -A signal trap
34d21
< complete -j -W '$(ps -x | tail +2 | cut -c1-5)' -P '%' wait
37d23
< complete -f -X '!*.Z' zmore
38a25,46
> complete -c eval
> complete -f chown
> complete -f gzip
> complete -W '"${GROUPS[@]}"' newgrp
> complete -A shopt shopt
> complete -A hostname ftp
> complete -A hostname rlogin
> complete -v getopts
> complete -c nice
> complete -c gdb
> complete -j -P '%' fg
> complete -f -X '!*.dvi' dvips
> complete -f -X '!*.texi*' texi2dvi
> complete -f .
> complete -v -S '=' declare
> complete -v -S '=' export
> complete -f -X '!*.dvi' xdvi
> complete -u su
> complete -o dirnames -o filenames -o nospace -d popd
> complete -A signal trap
> complete -j -W '$(ps -x | tail +2 | cut -c1-5)' -P '%' wait
> complete -f -X '!*.Z' zmore
48,49d55
< complete -c eval
< complete -f chown
53,54d58
< complete -f gzip
< complete -W '"${GROUPS[@]}"' newgrp
57,58d60
< complete -A shopt shopt
< complete -A hostname ftp
60,61d61
< complete -A hostname rlogin
< complete -v getopts
66,73c66,71
< ./complete.tests: line 132: compgen: -V: invalid option
< compgen: usage: compgen [-abcdefgjksuv] [-o option] [-A action] [-G globpat] [-W wordlist] [-F function] [-C command] [-X filterpat] [-P prefix] [-S suffix] [word]
< ./complete.tests: line 133: compgen: -V: invalid option
< compgen: usage: compgen [-abcdefgjksuv] [-o option] [-A action] [-G globpat] [-W wordlist] [-F function] [-C command] [-X filterpat] [-P prefix] [-S suffix] [word]
< 
< ./complete.tests: line 139: compgen: -V: invalid option
< compgen: usage: compgen [-abcdefgjksuv] [-o option] [-A action] [-G globpat] [-W wordlist] [-F function] [-C command] [-X filterpat] [-P prefix] [-S suffix] [word]
< 
---
> ./complete.tests: line 132: compgen: `invalid-name': not a valid identifier
> .
> unalias -- fee
> unalias -- fi
> unalias -- fum
> !
177c175
< autocd
---
> array_expand_once
178a177,178
> autocd
> bash_source_fullpath
203a204
> globskipdots
221a223
> noexpand_translation
222a225
> patsub_replacement
228a232
> varredir_close
378c382
< compgen: usage: compgen [-abcdefgjksuv] [-o option] [-A action] [-G globpat] [-W wordlist] [-F function] [-C command] [-X filterpat] [-P prefix] [-S suffix] [word]
---
> compgen: usage: compgen [-V varname] [-abcdefgjksuv] [-o option] [-A action] [-G globpat] [-W wordlist] [-F function] [-C command] [-X filterpat] [-P prefix] [-S suffix] [word]
381c385
< compgen: usage: compgen [-abcdefgjksuv] [-o option] [-A action] [-G globpat] [-W wordlist] [-F function] [-C command] [-X filterpat] [-P prefix] [-S suffix] [word]
---
> compgen: usage: compgen [-V varname] [-abcdefgjksuv] [-o option] [-A action] [-G globpat] [-W wordlist] [-F function] [-C command] [-X filterpat] [-P prefix] [-S suffix] [word]
run-comsub
1,20c1,21
< ./comsub.tests: line 20: hijkl: command not found
< ./comsub.tests: line 19: recho: command not found
< ./comsub.tests: line 21: recho: command not found
< ./comsub.tests: line 25: recho: command not found
< ./comsub.tests: line 27: recho: command not found
< ./comsub.tests: line 29: recho: command not found
< ./comsub.tests: line 31: recho: command not found
< ./comsub.tests: line 33: recho: command not found
< ./comsub.tests: line 37: recho: command not found
< ./comsub.tests: line 40: recho: command not found
< ./comsub.tests: line 43: recho: command not found
< 
< ./comsub.tests: line 46: recho: command not found
< 
< ./comsub.tests: line 50: recho: command not found
< 
< ./comsub.tests: line 52: recho: command not found
< 
< ./comsub.tests: line 56: recho: command not found
< 
---
> ./comsub.tests: line 19: hijkl: command not found
> argv[1] = <ab>
> argv[2] = <cd>
> argv[1] = <abmn>
> argv[2] = <opyz>
> argv[1] = <b>
> argv[1] = <a\>
> argv[2] = <b>
> argv[1] = <$>
> argv[2] = <bab>
> argv[1] = <`>
> argv[2] = <ab>
> argv[1] = <\>
> argv[2] = <ab>
> argv[1] = <foo \\^Jbar>
> argv[1] = <foo \^Jbar>
> argv[1] = <sed> argv[2] = <-e> argv[3] = <s/[^I:]/\^J/g>
> argv[1] = <sed> argv[2] = <-e> argv[3] = <s/[^I:]//g>
> argv[1] = <foo\^Jbar>
> argv[1] = <foobar>
> argv[1] = <foo\^Jbar>
24,26c25,26
< ./comsub.tests: line 84: --${ 
< }--: bad substitution
< ./comsub.tests: line 85: --${  }--: bad substitution
---
> blank ----
> blank ----
65,66c65,73
< ./comsub5.sub: line 26: syntax error near unexpected token `;;'
< ./comsub5.sub: line 26: `echo $( switch foo in foo) echo ok 2;; esac )'
---
> ok 2
> ok 3
> ok 4
> ok 5
> ok 6
> ok 7
> ok 9
> ok 8
> ok 8 
run-comsub-eof
1c1,3
< ./comsub-eof0.sub: line 7: warning: here-document at line 5 delimited by end-of-file (wanted `EOF')
---
> ./comsub-eof0.sub: line 4: warning: here-document at line 2 delimited by end-of-file (wanted `EOF')
> hi
> ./comsub-eof0.sub: line 11: warning: here-document at line 9 delimited by end-of-file (wanted `EOF')
3,4d4
< ./comsub-eof0.sub: line 9: unexpected EOF while looking for matching `)'
< ./comsub-eof0.sub: line 13: syntax error: unexpected end of file
8,10c8,10
< ./comsub-eof3.sub: line 1: unexpected EOF while looking for matching `)'
< ./comsub-eof3.sub: line 5: syntax error: unexpected end of file
< ./comsub-eof4.sub: line 6: warning: here-document at line 4 delimited by end-of-file (wanted `EOF')
---
> ./comsub-eof3.sub: line 4: warning: here-document at line 1 delimited by end-of-file (wanted `EOF')
> ./comsub-eof3.sub: line 5: unexpected EOF while looking for matching `)'
> ./comsub-eof4.sub: line 3: warning: here-document at line 1 delimited by end-of-file (wanted `EOF')
12c12,14
< ./comsub-eof5.sub: line 8: warning: here-document at line 6 delimited by end-of-file (wanted `)')
---
> ./comsub-eof5.sub: line 4: warning: here-document at line 2 delimited by end-of-file (wanted `)')
> hi
> ./comsub-eof5.sub: line 9: warning: here-document at line 7 delimited by end-of-file (wanted `EOF')
14c16
< ./comsub-eof5.sub: line 13: warning: here-document at line 11 delimited by end-of-file (wanted `EOF')
---
> ./comsub-eof5.sub: line 15: warning: here-document at line 13 delimited by end-of-file (wanted `)')
16,18c18
< ./comsub-eof5.sub: line 19: warning: here-document at line 17 delimited by end-of-file (wanted `)')
< ./comsub-eof5.sub: line 15: unexpected EOF while looking for matching `)'
< ./comsub-eof6.sub: line 1: unexpected EOF while looking for matching `)'
---
> ./comsub-eof6.sub: command substitution: line 3: unexpected EOF while looking for matching `)'
run-comsub-posix
34c34
< ./comsub-posix.tests: line 134: recho: command not found
---
> argv[1] = <abcde^J  >
36,38c36,39
< ./comsub-posix.tests: line 140: recho: command not found
< ./comsub-posix.tests: line 142: recho: command not found
< ./comsub-posix.tests: line 143: recho: command not found
---
> argv[1] = <abcde>
> argv[2] = <foo>
> argv[1] = <wxabcdeyz>
> argv[1] = <abcde>
61,63c62,63
< ./comsub-posix1.sub: command substitution: line 2: syntax error near unexpected token `)'
< ./comsub-posix1.sub: command substitution: line 2: ` if x; then echo foo )'
< should not see this
---
> ./comsub-posix1.sub: line 1: syntax error near unexpected token `)'
> ./comsub-posix1.sub: line 1: `echo $( if x; then echo foo )'
79,83c79,90
< ./comsub-posix5.sub: line 52: unexpected EOF while looking for matching `)'
< ./comsub-posix5.sub: line 71: syntax error: unexpected end of file
< case: command substitution: line 3: syntax error near unexpected token `esac'
< case: command substitution: line 3: ` esac ; bar=foo ; echo "$bar")'
< we should not see this
---
> bash: -c: line 1: syntax error near unexpected token `done' while looking for matching `)'
> bash: -c: line 1: `: $(case x in x) ;; x) done esac)'
> bash: -c: line 1: syntax error near unexpected token `done' while looking for matching `)'
> bash: -c: line 1: `: $(case x in x) ;; x) done ;; esac)'
> bash: -c: line 1: syntax error near unexpected token `esac' while looking for matching `)'
> bash: -c: line 1: `: $(case x in x) (esac) esac)'
> bash: -c: line 1: syntax error near unexpected token `in' while looking for matching `)'
> bash: -c: line 1: `: $(case x in esac|in) foo;; esac)'
> bash: -c: line 1: syntax error near unexpected token `done' while looking for matching `)'
> bash: -c: line 1: `: $(case x in x) ;; x) done)'
> case: -c: line 3: syntax error near unexpected token `esac' while looking for matching `)'
> case: -c: line 3: `$( esac ; bar=foo ; echo "$bar")) echo bad 2;;'
87,89c94,95
< syntax-error: command substitution: line 3: syntax error near unexpected token `done'
< syntax-error: command substitution: line 3: `case x in x) ;; x) done ;; esac)'
< after syntax error
---
> syntax-error: -c: line 2: syntax error near unexpected token `done' while looking for matching `)'
> syntax-error: -c: line 2: `: $(case x in x) ;; x) done ;; esac)'
run-comsub2
1,9c1,8
< ./comsub2.tests: line 19: ${ printf '%s\n' aa bb cc dd; }: bad substitution
< ./comsub2.tests: line 20: AA${ printf '%s\n' aa bb cc dd; }BB: bad substitution
< ./comsub2.tests: line 22: ${ printf '%s\n' aa bb cc dd; return; echo ee ff; }: bad substitution
< ./comsub2.tests: line 24: ${ printf '%s\n' aa bb cc dd
< 	}: bad substitution
< ./comsub2.tests: line 27: DDDDD${
< 	printf '%s\n' aa bb cc dd
< }EEEEE: bad substitution
< ./comsub2.tests: line 29: ${ printf '%s\n' aa bb cc dd; x=42 ; return 12; echo ee ff; }: bad substitution
---
> aa bb cc dd
> AAaa bb cc ddBB
> aa bb cc dd
> aa bb cc dd
> DDDDDaa bb cc ddEEEEE
> aa bb cc dd
> outside: 42
> aa bb cc dd
11c10,27
< ./comsub2.tests: line 32: ${ local x; printf '%s\n' aa bb cc dd; x=42 ; return 12; echo ee ff; }: bad substitution
---
> assignment: 12
> func () 
> { 
>     echo func-inside
> }
> abcde
> 67890
> 12345
> argv[1] = <>
> argv[1] = <>
> aa,bb
> JOBaa bb cc ddCONTROL
> ./comsub2.tests: line 68: p: command not found
> NOTFOUND
> ./comsub2.tests: line 75: p: command not found
> ./comsub2.tests: line 75: p: command not found
> expand_aliases      	off
> expand_aliases      	off
13,17c29,192
< ./comsub2.tests: line 34: ${ local x; printf '%s\n' aa bb cc dd; x=42 ; return 12; echo ee ff; }: bad substitution
< assignment: 1
< ./comsub2.tests: line 39: ${ :;}: bad substitution
< ./comsub2.tests: line 45: syntax error near unexpected token `}'
< ./comsub2.tests: line 45: `xx=${ func() { echo func-inside; }; }'
---
> ./comsub2.tests: line 79: alias: p: not found
> alias e='echo inside redefine'
> expand_aliases      	off
> 1
> expand_aliases      	on
> 2
> expand_aliases      	on
> outside:
> ./comsub2.tests: line 89: alias: p: not found
> expand_aliases      	on
> 1
> xx
> expand_aliases      	on
> 2
> xx
> expand_aliases      	on
> outside:
> expand_aliases      	on
> inside: 12 22 42
> outside: 42 2
> newlines
> 
> 
> outside: 42
> before: 1 2
> after: 2
> before: 1 2
> after: 2
> before: 1 2
> after: 1 2
> XnestedY
> a nested b
> one two
> 42
> 42
> 42
> 123
> 123
> 0
> 123
> 123
> 0
> Mon Aug 29 20:03:02 EDT 2022
> Mon Aug 29 20:03:02 EDT 2022
> Mon Aug 29 20:03:02 EDT 2022
> Mon Aug 29 20:03:02 EDT 2022
> 123
> before 123
> in for 123
> outside before: value
> inside before: value
> inside after: funsub
> inside: after false xxx
> outside after: funsub
> =====posix mode=====
> outside before: value
> .
> declare -a a=([0]="1" [1]="2" [2]="3" [3]="4")
> declare -- int="2"
> after here-doc: 1
> [1]-  Running                    sleep 1 &
> [2]+  Running                    sleep 1 &
> [1]-  Running                    sleep 1 &
> [2]+  Running                    sleep 1 &
> 17772 26794
> 17772 26794
> we should try rhs
> comsub
> and
> funsub
> in here-documents
> after all they work here
> and work here
> a b c == 1 2 3
>  == 1 2 3
> before return
> after func
> 1 2 3a b c
> 2 2
> foobara b c
> declare -- IFS=" "
> *???
> *???
> yyy zzzz
> argv[1] = <AA^ABB>
> argv[1] = <AA^OBB>
> argv[1] = <AA^?BB>
> argv[1] = <^A>
> argv[1] = <^A>
> argv[1] = <^A>
> argv[1] = <^A>
> argv[1] = <^A>
> argv[1] = <^A>
> argv[1] = <^?>
> argv[1] = <^?>
> argv[1] = <^?>
> argv[1] = <^?>
> argv[1] = <^?>
> argv[1] = <^?>
> argv[1] = <AA^ABB>
> argv[1] = <AA^ABB>
> argv[1] = <AA^OBB>
> argv[1] = <AA^OBB>
> argv[1] = <AA^?BB>
> argv[1] = <AA^?BB>
> argv[1] = <^A>
> argv[1] = <^A>
> argv[1] = <^A>
> argv[1] = <^A>
> argv[1] = <^A>
> argv[1] = <^A>
> argv[1] = <^A>
> argv[1] = <^A>
> argv[1] = <^A>
> argv[1] = <^A>
> argv[1] = <^?>
> argv[1] = <^?>
> argv[1] = <^?>
> argv[1] = <^?>
> argv[1] = <^?>
> argv[1] = <^?>
> argv[1] = <^?>
> argv[1] = <^?>
> argv[1] = <^?>
> argv[1] = <^?>
> argv[1] = <AA^ABB>
> argv[1] = <AA>
> argv[2] = <BB>
> argv[1] = <AA^ABB>
> argv[1] = <AA>
> argv[2] = <BB>
> argv[1] = <AA^?BB>
> argv[1] = <AA>
> argv[2] = <BB>
> argv[1] = <AA^?BB>
> argv[1] = <AA>
> argv[2] = <BB>
> argv[1] = <AA BB>
> argv[1] = <AA>
> argv[2] = <BB>
> argv[1] = <AA BB>
> argv[1] = <AA BB>
> argv[1] = <AA BB>
> argv[1] = <AA>
> argv[2] = <BB>
> argv[1] = <AA BB>
> argv[1] = <AA BB>
> inside1-inside2-outside
> BEFOREAA
> BB
> CC
> AFTER
> BEFOREAA
> BB
> CC
> AFTER
> unbalanced braces}}
> combined comsubs
> combined comsubs
> inside
> after: var = inside
> after: 42 var = inside
> var=inside 42
> after: 0 var = inside
run-cond
15c15,16
< returns: 1
---
> ./cond.tests: line 65: [[: X: integer expected
> returns: 2
31c32
< ./cond.tests: line 126: [[: 4+: syntax error: operand expected (error token is "+")
---
> ./cond.tests: line 126: [[: 4+: arithmetic syntax error: operand expected (error token is "+")
56,57c57,191
< ./cond.tests: line 230: syntax error near unexpected token `then'
< ./cond.tests: line 230: `if [[ str ]] then [[ str ]] fi'
---
> ok c1
> ok c2
> ok c3
> ok c4
> ok c5
> ok c6
> match 1
> match 2
> match 3
> match 4
> match 5
> match 6
> yes 1
> yes 2
> yes 3
> yes 4
> yes 5
> yes 6
> Dog 01 is Wiggles
> Dog 01 is Wiggles
> rematch 1
> matches 7
> matches 8
> matches 9
> unquoted matches
> match control-a 1
> match control-a 2
> match control-a 3
> match control-a 4
> match control-a 5
> ok 1
> ok 2
> ok 3
> ok 4
> ok 4a
> ok 5
> ok 6
> ok 7 -- d
> ok 8 -- o
> ok 9
> ok 10
> ok 11
> ok 12
> argv[1] = <\^?>
> 0
> 1
> 1
> 0
> 1
> 1
> 0
> 1
> 1
> [[ $'\001' =~ $'\001' ]] -> 0
> [[ $'\001' =~ $'\\\001' ]] -> 0
> [[ $'\001' =~ $'\\[\001]' ]] -> 1
> ---
> [[ $'\a' =~ $'\a' ]] -> 0
> [[ $'\a' =~ $'\\\a' ]] -> 0
> [[ $'\a' =~ $'\\[\a]' ]] -> 1
> ---
> [[ $'\177' =~ $'\177' ]] -> 0
> [[ $'\177' =~ $'\\\177' ]] -> 0
> [[ $'\177' =~ $'\\[\177]' ]] -> 1
> ---
> 0
> 1
> 1
> 0
> 1
> 1
> 0
> 1
> 1
> 0
> 1
> 0
> 1
> 1
> 0
> 0
> 0
> 1
> 1
> argv[1] = <^A>
> argv[2] = <^A>
> ok 1
> ok 2
> ok 3
> ok 4
> ok 5
> ok 6
> ok 7
> ok 8
> bash: -c: line 1: unexpected token `EOF', expected `)'
> bash: -c: line 2: syntax error: unexpected end of file from `[[' command on line 1
> bash: -c: line 1: unexpected EOF while looking for `]]'
> bash: -c: line 2: syntax error: unexpected end of file from `[[' command on line 1
> bash: -c: line 1: syntax error in conditional expression: unexpected token `]'
> bash: -c: line 1: syntax error near `]'
> bash: -c: line 1: `[[ ( -t X ) ]'
> bash: -c: line 1: unexpected argument `&' to conditional unary operator
> bash: -c: line 1: syntax error near `&'
> bash: -c: line 1: `[[ -n &'
> bash: -c: line 1: syntax error in conditional expression: unexpected token `&'
> bash: -c: line 1: syntax error near `&'
> bash: -c: line 1: `[[ -n XX &'
> bash: -c: line 1: syntax error in conditional expression: unexpected token `&'
> bash: -c: line 1: syntax error near `&'
> bash: -c: line 1: `[[ -n XX & ]'
> bash: -c: line 1: unexpected token `&', conditional binary operator expected
> bash: -c: line 1: syntax error near `&'
> bash: -c: line 1: `[[ 4 & ]]'
> bash: -c: line 1: unexpected argument `&' to conditional binary operator
> bash: -c: line 1: syntax error near `&'
> bash: -c: line 1: `[[ 4 > & ]]'
> bash: -c: line 1: unexpected token `&' in conditional command
> bash: -c: line 1: syntax error near `&'
> bash: -c: line 1: `[[ & ]]'
> bash: -c: line 1: unexpected token `7', conditional binary operator expected
> bash: -c: line 1: syntax error near `7'
> bash: -c: line 1: `[[ -Q 7 ]]'
> bash: -c: line 1: unexpected argument `<' to conditional unary operator
> bash: -c: line 1: syntax error near `<'
> bash: -c: line 1: `[[ -n < ]]'
> ERR: 22: -[[ -n $unset ]]- failed
> ERR: 28: -[[ -z nonempty ]]- failed
> + [[ -t X ]]
> ./cond-xtrace1.sub: line 6: [[: X: integer expected
> + [[ '' > 7 ]]
> + [[ -n X ]]
> + ivar=42
> + [[ 42 -eq 42 ]]
> + [[ -n a ]]
> + [[ -n b ]]
run-coproc
7,9c7,8
< ./coproc.tests: line 53: xcase: command not found
< 
< 
---
> FOO
> 63 60
11,15c10
< ./coproc.tests: line 70: ${COPROC[0]}: ambiguous redirect
< ./coproc.tests: line 71: ${COPROC[1]}: ambiguous redirect
< 
< ./coproc.tests: line 75: 4: Bad file descriptor
< 
---
> -1 -1
run-cprint
22c22
<     for name in $( echo 1 2 3 );
---
>     for name in $(echo 1 2 3);
run-dbg-support
run-dbg-support2
run-dirstack
run-dollars
1,56c1,73
< ./dollar-at-star: line 17: recho: command not found
< ./dollar-at-star: line 18: recho: command not found
< ./dollar-at-star: line 20: recho: command not found
< ./dollar-at-star: line 21: recho: command not found
< ./dollar-at-star: line 42: recho: command not found
< ./dollar-at-star: line 46: recho: command not found
< ./dollar-at-star: line 50: recho: command not found
< ./dollar-at-star: line 52: recho: command not found
< ./dollar-at-star: line 53: recho: command not found
< ./dollar-at-star: line 58: recho: command not found
< ./dollar-at-star: line 59: recho: command not found
< ./dollar-at-star: line 60: recho: command not found
< ./dollar-at-star: line 61: recho: command not found
< ./dollar-at-star: line 65: recho: command not found
< ./dollar-at-star: line 66: recho: command not found
< ./dollar-at-star: line 67: recho: command not found
< ./dollar-at-star: line 68: recho: command not found
< ./dollar-at-star: line 72: recho: command not found
< ./dollar-at-star: line 73: recho: command not found
< ./dollar-at-star: line 74: recho: command not found
< ./dollar-at-star: line 75: recho: command not found
< ./dollar-at-star: line 79: recho: command not found
< ./dollar-at-star: line 80: recho: command not found
< ./dollar-at-star: line 81: recho: command not found
< ./dollar-at-star: line 82: recho: command not found
< ./dollar-at-star: line 89: recho: command not found
< ./dollar-at-star: line 90: recho: command not found
< ./dollar-at-star: line 91: recho: command not found
< ./dollar-at-star: line 92: recho: command not found
< ./dollar-at-star: line 96: recho: command not found
< ./dollar-at-star: line 97: recho: command not found
< ./dollar-at-star: line 98: recho: command not found
< ./dollar-at-star: line 99: recho: command not found
< ./dollar-at-star: line 106: recho: command not found
< ./dollar-at-star: line 107: recho: command not found
< ./dollar-at-star: line 108: recho: command not found
< ./dollar-at-star: line 109: recho: command not found
< ./dollar-at-star: line 113: recho: command not found
< ./dollar-at-star: line 114: recho: command not found
< ./dollar-at-star: line 115: recho: command not found
< ./dollar-at-star: line 116: recho: command not found
< ./dollar-at-star: line 121: recho: command not found
< ./dollar-at-star: line 122: recho: command not found
< ./dollar-at-star: line 123: recho: command not found
< ./dollar-at-star: line 124: recho: command not found
< ./dollar-at-star: line 128: recho: command not found
< ./dollar-at-star: line 129: recho: command not found
< ./dollar-at-star: line 130: recho: command not found
< ./dollar-at-star: line 131: recho: command not found
< ./dollar-at-star: line 137: recho: command not found
< ./dollar-at-star: line 138: recho: command not found
< ./dollar-at-star: line 143: recho: command not found
< ./dollar-at-star: line 144: recho: command not found
< ./dollar-at-star: line 148: recho: command not found
< ./dollar-at-star: line 149: recho: command not found
< ./dollar-at-star: line 150: recho: command not found
---
> argv[1] = <>
> argv[1] = <a b>
> argv[1] = <ab>
> argv[1] = <a b>
> argv[1] = <a>
> argv[2] = <b>
> argv[1] = <a>
> argv[2] = <b>
> argv[1] = <3>
> argv[1] = <bob>
> argv[1] = <tom dick harry>
> argv[1] = <joe>
> argv[1] = <3>
> argv[1] = <bob>
> argv[1] = <tom dick harry>
> argv[1] = <joe>
> argv[1] = <3>
> argv[1] = <bob>
> argv[1] = <tom dick harry>
> argv[1] = <joe>
> argv[1] = <3>
> argv[1] = <bob>
> argv[1] = <tom dick harry>
> argv[1] = <joe>
> argv[1] = <3>
> argv[1] = <bob>
> argv[1] = <tom dick harry>
> argv[1] = <joe>
> argv[1] = <3>
> argv[1] = <bob>
> argv[1] = <tom dick harry>
> argv[1] = <joe>
> argv[1] = <5>
> argv[1] = <bob>
> argv[1] = <tom>
> argv[1] = <dick>
> argv[1] = <5>
> argv[1] = <bob>
> argv[1] = <tom>
> argv[1] = <dick>
> argv[1] = <1>
> argv[1] = <bob>
> argv[2] = <tom>
> argv[3] = <dick>
> argv[4] = <harry>
> argv[5] = <joe>
> argv[1] = <3>
> argv[1] = <bob>
> argv[1] = <tom>
> argv[2] = <dick>
> argv[3] = <harry>
> argv[1] = <joe>
> argv[1] = <a>
> argv[2] = <b>
> argv[3] = <c>
> argv[4] = <d>
> argv[5] = <e>
> argv[1] = <a>
> argv[2] = <b>
> argv[3] = <c>
> argv[4] = <d>
> argv[5] = <e>
> argv[1] = <foo>
> argv[2] = <bar>
> argv[3] = <bam>
> argv[1] = <foobarbam>
> argv[1] = <foo>
> argv[2] = <bar>
> argv[3] = <bam>
> argv[1] = <foo>
> argv[2] = <bar>
> argv[3] = <bam>
> argv[1] = <foo bar bam>
142,152c159,169
< ./dollar-at-star3.sub: line 17: recho: command not found
< ./dollar-at-star3.sub: line 20: recho: command not found
< ./dollar-at-star3.sub: line 23: recho: command not found
< ./dollar-at-star3.sub: line 26: recho: command not found
< ./dollar-at-star3.sub: line 29: recho: command not found
< ./dollar-at-star3.sub: line 32: recho: command not found
< ./dollar-at-star3.sub: line 35: recho: command not found
< ./dollar-at-star3.sub: line 40: recho: command not found
< ./dollar-at-star3.sub: line 43: recho: command not found
< ./dollar-at-star3.sub: line 46: recho: command not found
< ./dollar-at-star3.sub: line 51: recho: command not found
---
> argv[1] = <a>
> argv[1] = <a>
> argv[1] = <a>
> argv[1] = <a>
> argv[1] = <a>
> argv[1] = <a>
> argv[1] = <a>
> argv[1] = <one>
> argv[1] = <o>
> argv[1] = <o>
> argv[1] = <one>
175,179c192,197
< ./dollar-at-star4.sub: line 87: recho: command not found
< ./dollar-at-star4.sub: line 89: recho: command not found
< ./dollar-at-star4.sub: line 90: recho: command not found
< ./dollar-at-star4.sub: line 95: recho: command not found
< ./dollar-at-star4.sub: line 96: recho: command not found
---
> argv[1] = <a b>
> argv[1] = <abcd>
> argv[1] = <abcd>
> argv[1] = <a>
> argv[2] = <b>
> argv[1] = <a b>
197d214
< ./dollar-at-star5.sub: line 36: recho: command not found
199d215
< ./dollar-at-star5.sub: line 39: recho: command not found
201d216
< ./dollar-at-star5.sub: line 42: recho: command not found
204c219
< ./dollar-at-star5.sub: line 47: recho: command not found
---
> argv[1] = <>
206c221
< ./dollar-at-star5.sub: line 49: recho: command not found
---
> argv[1] = <>
208,209c223,224
< ./dollar-at-star5.sub: line 52: recho: command not found
< ./dollar-at-star5.sub: line 53: recho: command not found
---
> argv[1] = <>
> argv[1] = <>
212c227
< ./dollar-at-star5.sub: line 57: recho: command not found
---
> argv[1] = <>
214c229
< ./dollar-at-star5.sub: line 59: recho: command not found
---
> argv[1] = <>
216c231
< ./dollar-at-star5.sub: line 62: recho: command not found
---
> argv[1] = <>
218c233
< ./dollar-at-star5.sub: line 64: recho: command not found
---
> argv[1] = <>
220,230c235,271
< ./dollar-at-star5.sub: line 66: recho: command not found
< ./dollar-at-star6.sub: line 17: recho: command not found
< ./dollar-at-star6.sub: line 18: recho: command not found
< ./dollar-at-star6.sub: line 21: recho: command not found
< ./dollar-at-star6.sub: line 22: recho: command not found
< ./dollar-at-star6.sub: line 28: recho: command not found
< ./dollar-at-star6.sub: line 29: recho: command not found
< ./dollar-at-star6.sub: line 34: recho: command not found
< ./dollar-at-star6.sub: line 35: recho: command not found
< ./dollar-at-star6.sub: line 41: recho: command not found
< ./dollar-at-star6.sub: line 42: recho: command not found
---
> argv[1] = <'a'>
> argv[2] = <'b'>
> argv[3] = <'c'>
> argv[1] = <'a'>
> argv[2] = <'b'>
> argv[3] = <'c'>
> argv[1] = <>
> argv[2] = <a>
> argv[3] = <>
> argv[4] = <>
> argv[5] = <b>
> argv[6] = <>
> argv[7] = <>
> argv[8] = <c>
> argv[1] = <'a'>
> argv[2] = <'b'>
> argv[3] = <'c'>
> argv[1] = <>
> argv[2] = <a>
> argv[3] = <>
> argv[4] = <>
> argv[5] = <b>
> argv[6] = <>
> argv[7] = <>
> argv[8] = <c>
> argv[1] = <'a'>
> argv[2] = <'b'>
> argv[3] = <'c'>
> argv[1] = <>
> argv[2] = <a>
> argv[1] = <'a'>
> argv[1] = <'a'>
> argv[2] = <'b'>
> argv[3] = <'c'>
> argv[1] = <'a'>
> argv[2] = <'b'>
> argv[3] = <'c'>
264,430c305,468
< ./dollar-at-star9.sub: line 16: recho: command not found
< ./dollar-at-star9.sub: line 17: recho: command not found
< ./dollar-at-star9.sub: line 22: recho: command not found
< ./dollar-at-star9.sub: line 23: recho: command not found
< ./dollar-at-star9.sub: line 30: recho: command not found
< ./dollar-at-star9.sub: line 31: recho: command not found
< ./dollar-at-star9.sub: line 33: recho: command not found
< ./dollar-at-star9.sub: line 34: recho: command not found
< ./dollar-at-star9.sub: line 36: recho: command not found
< ./dollar-at-star9.sub: line 37: recho: command not found
< ./dollar-at-star9.sub: line 39: recho: command not found
< ./dollar-at-star9.sub: line 40: recho: command not found
< ./dollar-at-star9.sub: line 42: recho: command not found
< ./dollar-at-star9.sub: line 43: recho: command not found
< ./dollar-at-star9.sub: line 47: recho: command not found
< ./dollar-at-star9.sub: line 48: recho: command not found
< ./dollar-at-star9.sub: line 50: recho: command not found
< ./dollar-at-star9.sub: line 51: recho: command not found
< ./dollar-at-star9.sub: line 53: recho: command not found
< ./dollar-at-star9.sub: line 54: recho: command not found
< ./dollar-at-star9.sub: line 56: recho: command not found
< ./dollar-at-star9.sub: line 57: recho: command not found
< ./dollar-at-star9.sub: line 65: recho: command not found
< ./dollar-at-star9.sub: line 66: recho: command not found
< ./dollar-at-star9.sub: line 67: recho: command not found
< ./dollar-at-star9.sub: line 69: recho: command not found
< ./dollar-at-star9.sub: line 70: recho: command not found
< ./dollar-at-star9.sub: line 71: recho: command not found
< ./dollar-at-star9.sub: line 73: recho: command not found
< ./dollar-at-star9.sub: line 74: recho: command not found
< ./dollar-at-star9.sub: line 76: recho: command not found
< ./dollar-at-star9.sub: line 77: recho: command not found
< ./dollar-at-star9.sub: line 79: recho: command not found
< ./dollar-at-star9.sub: line 80: recho: command not found
< ./dollar-at-star9.sub: line 83: recho: command not found
< ./dollar-at-star9.sub: line 84: recho: command not found
< ./dollar-at-star9.sub: line 86: recho: command not found
< ./dollar-at-star9.sub: line 87: recho: command not found
< ./dollar-at-star9.sub: line 89: recho: command not found
< ./dollar-at-star9.sub: line 90: recho: command not found
< ./dollar-at-star9.sub: line 100: recho: command not found
< ./dollar-at-star9.sub: line 101: recho: command not found
< ./dollar-at-star9.sub: line 102: recho: command not found
< ./dollar-at-star9.sub: line 104: recho: command not found
< ./dollar-at-star9.sub: line 105: recho: command not found
< ./dollar-at-star9.sub: line 106: recho: command not found
< ./dollar-at-star9.sub: line 108: recho: command not found
< ./dollar-at-star9.sub: line 109: recho: command not found
< ./dollar-at-star9.sub: line 111: recho: command not found
< ./dollar-at-star9.sub: line 112: recho: command not found
< ./dollar-at-star9.sub: line 114: recho: command not found
< ./dollar-at-star9.sub: line 115: recho: command not found
< ./dollar-at-star9.sub: line 118: recho: command not found
< ./dollar-at-star9.sub: line 119: recho: command not found
< ./dollar-at-star9.sub: line 121: recho: command not found
< ./dollar-at-star9.sub: line 122: recho: command not found
< ./dollar-at-star9.sub: line 124: recho: command not found
< ./dollar-at-star9.sub: line 125: recho: command not found
< ./dollar-at-star9.sub: line 136: recho: command not found
< ./dollar-at-star9.sub: line 137: recho: command not found
< ./dollar-at-star9.sub: line 141: recho: command not found
< ./dollar-at-star9.sub: line 142: recho: command not found
< ./dollar-at-star9.sub: line 152: recho: command not found
< ./dollar-at-star9.sub: line 153: recho: command not found
< ./dollar-at-star9.sub: line 157: recho: command not found
< ./dollar-at-star9.sub: line 158: recho: command not found
< ./dollar-at-star9.sub: line 162: recho: command not found
< ./dollar-at-star9.sub: line 163: recho: command not found
< ./dollar-at-star9.sub: line 174: recho: command not found
< ./dollar-at-star9.sub: line 175: recho: command not found
< ./dollar-at-star9.sub: line 179: recho: command not found
< ./dollar-at-star9.sub: line 180: recho: command not found
< ./dollar-at-star9.sub: line 184: recho: command not found
< ./dollar-at-star9.sub: line 185: recho: command not found
< ./dollar-at-star9.sub: line 193: recho: command not found
< ./dollar-at-star9.sub: line 194: recho: command not found
< ./dollar-at-star9.sub: line 200: recho: command not found
< ./dollar-at-star9.sub: line 201: recho: command not found
< ./dollar-at-star9.sub: line 209: recho: command not found
< ./dollar-at-star9.sub: line 210: recho: command not found
< ./dollar-at-star9.sub: line 214: recho: command not found
< ./dollar-at-star9.sub: line 215: recho: command not found
< ./dollar-at-star9.sub: line 225: recho: command not found
< ./dollar-at-star9.sub: line 226: recho: command not found
< ./dollar-at-star9.sub: line 232: recho: command not found
< ./dollar-at-star9.sub: line 233: recho: command not found
< ./dollar-at-star9.sub: line 240: recho: command not found
< ./dollar-at-star9.sub: line 242: recho: command not found
< ./dollar-at-star9.sub: line 245: recho: command not found
< ./dollar-at-star9.sub: line 246: recho: command not found
< ./dollar-at-star9.sub: line 252: recho: command not found
< ./dollar-at-star9.sub: line 255: recho: command not found
< ./dollar-at-star9.sub: line 261: recho: command not found
< ./dollar-at-star9.sub: line 263: recho: command not found
< ./dollar-at-star9.sub: line 266: recho: command not found
< ./dollar-at-star9.sub: line 267: recho: command not found
< ./dollar-at-star9.sub: line 273: recho: command not found
< ./dollar-at-star9.sub: line 277: recho: command not found
< ./dollar-at-star9.sub: line 278: recho: command not found
< ./dollar-at-star10.sub: line 8: recho: command not found
< ./dollar-at-star10.sub: line 9: recho: command not found
< ./dollar-at-star10.sub: line 11: recho: command not found
< ./dollar-at-star10.sub: line 12: recho: command not found
< ./dollar-at-star10.sub: line 14: recho: command not found
< ./dollar-at-star10.sub: line 15: recho: command not found
< ./dollar-at-star10.sub: line 19: recho: command not found
< ./dollar-at-star10.sub: line 20: recho: command not found
< ./dollar-at-star10.sub: line 22: recho: command not found
< ./dollar-at-star10.sub: line 23: recho: command not found
< ./dollar-at-star10.sub: line 25: recho: command not found
< ./dollar-at-star10.sub: line 26: recho: command not found
< ./dollar-at-star10.sub: line 31: recho: command not found
< ./dollar-at-star10.sub: line 32: recho: command not found
< ./dollar-at-star10.sub: line 33: recho: command not found
< ./dollar-at-star10.sub: line 35: recho: command not found
< ./dollar-at-star10.sub: line 36: recho: command not found
< ./dollar-at-star10.sub: line 37: recho: command not found
< ./dollar-at-star10.sub: line 42: recho: command not found
< ./dollar-at-star10.sub: line 43: recho: command not found
< ./dollar-at-star10.sub: line 51: recho: command not found
< ./dollar-at-star10.sub: line 52: recho: command not found
< ./dollar-at-star10.sub: line 54: recho: command not found
< ./dollar-at-star10.sub: line 55: recho: command not found
< ./dollar-at-star10.sub: line 57: recho: command not found
< ./dollar-at-star10.sub: line 58: recho: command not found
< ./dollar-at-star10.sub: line 61: recho: command not found
< ./dollar-at-star10.sub: line 62: recho: command not found
< ./dollar-at-star10.sub: line 64: recho: command not found
< ./dollar-at-star10.sub: line 65: recho: command not found
< ./dollar-at-star11.sub: line 6: recho: command not found
< ./dollar-at-star11.sub: line 7: recho: command not found
< ./dollar-at-star11.sub: line 8: recho: command not found
< ./dollar-at-star11.sub: line 10: recho: command not found
< ./dollar-at-star11.sub: line 11: recho: command not found
< ./dollar-at-star11.sub: line 13: recho: command not found
< ./dollar-at-star11.sub: line 14: recho: command not found
< ./dollar-at-star11.sub: line 15: recho: command not found
< ./dollar-at-star11.sub: line 17: recho: command not found
< ./dollar-at-star11.sub: line 18: recho: command not found
< ./dollar-at-star11.sub: line 20: recho: command not found
< ./dollar-at-star11.sub: line 21: recho: command not found
< ./dollar-at-star11.sub: line 22: recho: command not found
< ./dollar-at-star11.sub: line 24: recho: command not found
< ./dollar-at-star11.sub: line 25: recho: command not found
< ./dollar-at-star11.sub: line 27: recho: command not found
< ./dollar-at-star11.sub: line 31: recho: command not found
< ./dollar-at-star11.sub: line 32: recho: command not found
< ./dollar-at-star11.sub: line 34: recho: command not found
< ./dollar-at-star11.sub: line 35: recho: command not found
< ./dollar-at-star11.sub: line 41: recho: command not found
< ./dollar-at-star11.sub: line 42: recho: command not found
< ./dollar-at-star11.sub: line 44: recho: command not found
< ./dollar-at-star11.sub: line 45: recho: command not found
< ./dollar-at-star11.sub: line 49: recho: command not found
< ./dollar-at-star11.sub: line 50: recho: command not found
< ./dollar-at-star11.sub: line 51: recho: command not found
< ./dollar-at-star11.sub: line 53: recho: command not found
< ./dollar-at-star11.sub: line 54: recho: command not found
< ./dollar-at-star11.sub: line 56: recho: command not found
< ./dollar-at-star11.sub: line 57: recho: command not found
< ./dollar-at-star11.sub: line 58: recho: command not found
< ./dollar-at-star11.sub: line 60: recho: command not found
< ./dollar-at-star11.sub: line 61: recho: command not found
< ./dollar-at-star11.sub: line 70: recho: command not found
< ./dollar-at-star11.sub: line 74: recho: command not found
< ./dollar-at-star11.sub: line 74: recho: command not found
< 1:0
---
> argv[1] = <  >
> argv[1] = <  >
> argv[1] = <  >
> argv[1] = <  >
> argv[1] = <  >
> argv[1] = <  >
> argv[1] = <  >
> argv[1] = <  >
> argv[1] = <   >
> argv[1] = <   >
> argv[1] = <  >
> argv[1] = <  >
> argv[1] = <  >
> argv[1] = < X >
> argv[1] = < X >
> argv[1] = < X >
> argv[1] = < X >
> argv[1] = < X >
> argv[1] = < X >
> argv[1] = < X >
> argv[1] = <>
> argv[1] = < X >
> argv[1] = <>
> argv[1] = < X >
> argv[1] = <>
> argv[1] = < X >
> argv[1] = < X >
> argv[1] = < X >
> argv[1] = < X >
> argv[1] = < X >
> argv[1] = < X >
> argv[1] = < X>
> argv[2] = <Y >
> argv[1] = < X>
> argv[2] = <Y >
> argv[1] = < X>
> argv[2] = <Y >
> argv[1] = < X Y >
> argv[1] = < X Y >
> argv[1] = < X Y >
> argv[1] = < X Y >
> argv[1] = < X Y >
> argv[1] = < X Y >
> argv[1] = < X Y >
> argv[1] = < XY >
> argv[1] = < XY >
> argv[1] = < X Y >
> argv[1] = < X Y >
> argv[1] = < X Y >
> argv[1] = < X Y >
> argv[1] = < X Y >
> argv[1] = < X Y >
> argv[1] = < X >
> argv[1] = < X >
> argv[1] = < X >
> argv[1] = < X >
> argv[1] = <ba>
> argv[1] = <ba>
> argv[1] = <ba>
> argv[1] = <b>
> argv[2] = <a>
> argv[1] = <a:b>
> argv[1] = <a:b>
> argv[1] = <a>
> argv[2] = <b>
> argv[1] = <a>
> argv[2] = <b>
> argv[1] = <a>
> argv[2] = <b>
> argv[1] = <a>
> argv[2] = <b>
> argv[1] = < X >
> argv[1] = < X >
> argv[1] = < X >
> argv[1] = < X >
> argv[1] = <a>
> argv[2] = <b>
> argv[1] = <a>
> argv[2] = <b>
> argv[1] = <a>
> argv[2] = <b>
> argv[1] = <a>
> argv[2] = <b>
> argv[1] = < X >
> argv[1] = < X >
> argv[1] = < X >
> argv[1] = < X >
> argv[1] = <^?>
> argv[1] = <>
> argv[1] = <>
> argv[1] = <>
> argv[1] = <^?>
> argv[1] = <^?>
> argv[1] = <^?>
> argv[1] = <^?>
> argv[1] = <>
> argv[1] = <>
> argv[1] = <>
> argv[1] = <>
> argv[1] = <>
> argv[1] = <>
> argv[1] = <>
> argv[1] = <>
> argv[1] = <>
> argv[1] = <>
> argv[1] = <>
> argv[1] = <>
> argv[1] = <>
> argv[1] = <>
> argv[1] = <^?>
> argv[1] = <^?>
> argv[1] = <nonnull>
> argv[1] = <^?>
> argv[1] = <^?>
> argv[1] = <nonnull>
> argv[1] = <>
> argv[1] = <>
> argv[1] = <>
> argv[1] = <>
> argv[1] = <>
> argv[1] = <>
> argv[1] = <>
> argv[1] = <>
> argv[1] = <>
> argv[1] = <>
> argv[1] = <>
> argv[1] = <>
> argv[1] = <>
> argv[1] = <>
> argv[1] = <>
> argv[1] = <>
> argv[1] = <>
> argv[1] = <>
> argv[1] = <>
> argv[1] = <>
> argv[1] = <>
> argv[1] = <>
> argv[1] = <>
> argv[1] = <>
> argv[1] = <>
> argv[1] = <>
> argv[1] = </>
> argv[1] = </>
> argv[1] = </>
> argv[1] = </>
> argv[1] = <>
> argv[1] = <>
> argv[1] = <>
> argv[1] = <>
> argv[1] = <''>
> argv[1] = <''>
> argv[1] = <''>
> argv[1] = <''>
> argv[1] = <''>
> argv[1] = <>
> argv[1] = <>
> argv[1] = <>
> argv[1] = <>
> argv[1] = <>
> argv[1] = <>
> argv[1] = <>
> argv[1] = <>
> argv[1] = </>
> 1:1
455,472c493,522
< ./dollar-at2.sub: line 18: recho: command not found
< ./dollar-at2.sub: line 18: recho: command not found
< ./dollar-at2.sub: line 25: recho: command not found
< ./dollar-at2.sub: line 25: recho: command not found
< ./dollar-star2.sub: line 21: recho: command not found
< ./dollar-star2.sub: line 22: recho: command not found
< ./dollar-star2.sub: line 33: recho: command not found
< ./dollar-star2.sub: line 34: recho: command not found
< ./dollar-star2.sub: line 36: recho: command not found
< ./dollar-star2.sub: line 37: recho: command not found
< ./dollar-star2.sub: line 38: recho: command not found
< ./dollar-star2.sub: line 39: recho: command not found
< ./dollar-star3.sub: line 22: recho: command not found
< ./dollar-star3.sub: line 23: recho: command not found
< ./dollar-star3.sub: line 25: recho: command not found
< ./dollar-star3.sub: line 26: recho: command not found
< ./dollar-star3.sub: line 28: recho: command not found
< ./dollar-star3.sub: line 29: recho: command not found
---
> argv[1] = <echo 1 ; echo 1>
> argv[1] = <echo 1 2 ; echo 1>
> argv[2] = <2>
> argv[1] = <echo 1 ; echo 1>
> argv[1] = <echo 1 2 ; echo 1>
> argv[2] = <2>
> argv[1] = <AB>
> argv[1] = <AB>
> argv[1] = <A BC D>
> argv[1] = <A BC D>
> argv[1] = <A BC D>
> argv[1] = <A B>
> argv[2] = <C D>
> argv[1] = <A BC D>
> argv[1] = <A BC D>
> argv[1] = <fooq//barq/>
> argv[1] = <fooq>
> argv[2] = <>
> argv[3] = <barq>
> argv[4] = <>
> argv[1] = <foo!//bar!/>
> argv[1] = <foo!>
> argv[2] = <>
> argv[3] = <bar!>
> argv[4] = <>
> argv[1] = <ooq//arq/>
> argv[1] = <ooq>
> argv[2] = <>
> argv[3] = <arq>
> argv[4] = <>
490,493c540,547
< ./dollar-at4.sub: line 3: recho: command not found
< ./dollar-at4.sub: line 4: recho: command not found
< ./dollar-at4.sub: line 9: recho: command not found
< ./dollar-at4.sub: line 10: recho: command not found
---
> argv[1] = <a  b>
> argv[2] = <c  d>
> argv[1] = <a>
> argv[2] = <b>
> argv[3] = <c>
> argv[4] = <d>
> argv[1] = <a  b c  d>
> argv[1] = <a  b c  d>
545,546c599,602
< ./dollar-at6.sub: line 16: recho: command not found
< ./dollar-at6.sub: line 17: recho: command not found
---
> argv[1] = <>
> argv[2] = <x>
> argv[1] = <>
> argv[2] = <x>
548,568c604,631
< ./dollar-at6.sub: line 24: recho: command not found
< ./dollar-at6.sub: line 25: recho: command not found
< ./dollar-at6.sub: line 29: recho: command not found
< ./dollar-at6.sub: line 31: recho: command not found
< ./dollar-at6.sub: line 33: recho: command not found
< ./dollar-at6.sub: line 37: recho: command not found
< ./dollar-at6.sub: line 38: recho: command not found
< ./dollar-at6.sub: line 42: recho: command not found
< ./dollar-at6.sub: line 43: recho: command not found
< ./dollar-star6.sub: line 14: recho: command not found
< ./dollar-star6.sub: line 15: recho: command not found
< ./dollar-star6.sub: line 16: recho: command not found
< ./dollar-star6.sub: line 20: recho: command not found
< ./dollar-star6.sub: line 21: recho: command not found
< ./dollar-star6.sub: line 22: recho: command not found
< ./dollar-star6.sub: line 26: recho: command not found
< ./dollar-star6.sub: line 27: recho: command not found
< ./dollar-star6.sub: line 28: recho: command not found
< ./dollar-star6.sub: line 30: recho: command not found
< ./dollar-star6.sub: line 31: recho: command not found
< ./dollar-star6.sub: line 32: recho: command not found
---
> argv[1] = <>
> argv[2] = <>
> argv[3] = <x>
> argv[1] = <>
> argv[2] = <x>
> argv[1] = <>
> argv[2] = <>
> argv[3] = <x>
> argv[1] = <>
> argv[2] = <x>
> argv[1] = <>
> argv[2] = <x>
> argv[1] = <>
> argv[1] = <>
> argv[1] = <>
> argv[1] = <>
> argv[1] = <AwR>
> argv[1] = <AwR>
> argv[1] = <AR>
> argv[1] = <AwR>
> argv[1] = <AR>
> argv[1] = <AR>
> argv[1] = <AwR>
> argv[1] = <AwR>
> argv[1] = <A^?R>
> argv[1] = <AwR>
> argv[1] = <AwR>
> argv[1] = <A^?R>
571c634
< ./dollar-star7.sub: line 27: recho: command not found
---
> argv[1] = <a-b-c>
574,578c637,647
< ./dollar-star7.sub: line 35: recho: command not found
< ./dollar-star7.sub: line 38: recho: command not found
< ./dollar-star7.sub: line 39: recho: command not found
< ./dollar-star7.sub: line 42: recho: command not found
< ./dollar-star7.sub: line 43: recho: command not found
---
> argv[1] = <a-b c-d>
> argv[1] = <a>
> argv[2] = <b>
> argv[3] = <c>
> argv[4] = <d>
> argv[1] = <a b c d>
> argv[1] = <a>
> argv[2] = <b>
> argv[3] = <c>
> argv[4] = <d>
> argv[1] = <a b c d>
609,612c678,685
< ./dollar-at7.sub: line 16: recho: command not found
< ./dollar-at7.sub: line 17: recho: command not found
< ./dollar-at7.sub: line 19: recho: command not found
< ./dollar-at7.sub: line 20: recho: command not found
---
> argv[1] = <1>
> argv[2] = <>
> argv[1] = <2>
> argv[2] = <>
> argv[1] = <3>
> argv[2] = <>
> argv[1] = <4>
> argv[2] = <>
614,617c687,693
< ./dollar-at7.sub: line 25: recho: command not found
< ./dollar-at7.sub: line 26: recho: command not found
< ./dollar-at7.sub: line 28: recho: command not found
< ./dollar-at7.sub: line 29: recho: command not found
---
> argv[1] = <1>
> argv[2] = <>
> argv[1] = <2>
> argv[2] = <>
> argv[1] = <3>
> argv[1] = <4>
> argv[2] = <>
619,624c695,706
< ./dollar-at7.sub: line 34: recho: command not found
< ./dollar-at7.sub: line 35: recho: command not found
< ./dollar-at7.sub: line 37: recho: command not found
< ./dollar-at7.sub: line 39: recho: command not found
< ./dollar-at7.sub: line 40: recho: command not found
< ./dollar-at7.sub: line 42: recho: command not found
---
> argv[1] = <1>
> argv[2] = <>
> argv[1] = <2>
> argv[2] = <>
> argv[1] = <3>
> argv[2] = <>
> argv[1] = <4>
> argv[2] = <>
> argv[1] = <5>
> argv[2] = <>
> argv[1] = <6>
> argv[2] = <>
626,631c708,719
< ./dollar-at7.sub: line 47: recho: command not found
< ./dollar-at7.sub: line 48: recho: command not found
< ./dollar-at7.sub: line 50: recho: command not found
< ./dollar-at7.sub: line 52: recho: command not found
< ./dollar-at7.sub: line 53: recho: command not found
< ./dollar-at7.sub: line 55: recho: command not found
---
> argv[1] = <1>
> argv[2] = <>
> argv[1] = <2>
> argv[2] = <>
> argv[1] = <3>
> argv[2] = <>
> argv[1] = <4>
> argv[2] = <>
> argv[1] = <5>
> argv[2] = <>
> argv[1] = <6>
> argv[2] = <>
633,634c721,724
< ./dollar-at7.sub: line 58: recho: command not found
< ./dollar-at7.sub: line 59: recho: command not found
---
> argv[1] = <1>
> argv[2] = <>
> argv[1] = <2>
> argv[2] = <>
641,645c731,738
< ./dollar-star9.sub: line 43: recho: command not found
< ./dollar-star9.sub: line 44: recho: command not found
< ./dollar-star9.sub: line 45: recho: command not found
< ./dollar-star9.sub: line 46: recho: command not found
< ./dollar-star9.sub: line 49: recho: command not found
---
> argv[1] = <1>
> argv[2] = <2>
> argv[1] = <1>
> argv[2] = <2>
> argv[1] = <1 2>
> argv[1] = <1 2>
> argv[1] = <1>
> argv[2] = <2>
647c740,741
< ./dollar-star9.sub: line 52: recho: command not found
---
> argv[1] = <1>
> argv[2] = <2>
649,692c743,747
< ./dollar-star9.sub: line 56: recho: command not found
< ./dollar-star9.sub: line 59: recho: command not found
< ./dollar-star10.sub: line 19: recho: command not found
< ./dollar-star10.sub: line 20: recho: command not found
< ./dollar-star10.sub: line 22: recho: command not found
< ./dollar-star10.sub: line 23: recho: command not found
< ./dollar-star10.sub: line 25: recho: command not found
< ./dollar-star10.sub: line 26: recho: command not found
< ./dollar-star10.sub: line 28: recho: command not found
< ./dollar-star10.sub: line 29: recho: command not found
< ./dollar-star10.sub: line 31: recho: command not found
< ./dollar-star10.sub: line 32: recho: command not found
< ./dollar-star10.sub: line 34: recho: command not found
< ./dollar-star10.sub: line 35: recho: command not found
< ./dollar-star10.sub: line 37: recho: command not found
< ./dollar-star10.sub: line 38: recho: command not found
< ./dollar-star10.sub: line 40: recho: command not found
< ./dollar-star10.sub: line 41: recho: command not found
< ./dollar-star10.sub: line 46: recho: command not found
< ./dollar-star10.sub: line 47: recho: command not found
< ./dollar-star10.sub: line 49: recho: command not found
< ./dollar-star10.sub: line 50: recho: command not found
< ./dollar-star10.sub: line 52: recho: command not found
< ./dollar-star10.sub: line 53: recho: command not found
< ./dollar-star10.sub: line 55: recho: command not found
< ./dollar-star10.sub: line 56: recho: command not found
< ./dollar-star10.sub: line 58: recho: command not found
< ./dollar-star10.sub: line 59: recho: command not found
< ./dollar-star10.sub: line 61: recho: command not found
< ./dollar-star10.sub: line 62: recho: command not found
< ./dollar-star10.sub: line 64: recho: command not found
< ./dollar-star10.sub: line 65: recho: command not found
< ./dollar-star10.sub: line 67: recho: command not found
< ./dollar-star10.sub: line 68: recho: command not found
< ./dollar-star10.sub: line 77: recho: command not found
< ./dollar-star10.sub: line 79: recho: command not found
< ./dollar-star10.sub: line 81: recho: command not found
< ./dollar-star10.sub: line 83: recho: command not found
< ./dollar-star10.sub: line 86: recho: command not found
< ./dollar-star10.sub: line 88: recho: command not found
< ./dollar-star10.sub: line 90: recho: command not found
< ./dollar-star10.sub: line 92: recho: command not found
< ./dollar-star11.sub: line 17: recho: command not found
< ./dollar-star11.sub: line 18: recho: command not found
---
> argv[1] = <1 2>
> argv[1] = <1 2>
> argv[1] = <^Aaa^Abb^Acc^A--^Add^A>
> argv[1] = <^A--^A>
> ok 1
693a749,751
> ok 3
> ok 4
> ok 5
698a757,760
> ok 11
> ok 12
> ok 13
> ok 14
703a766
> ok 20
704a768,769
> ok 22
> ok 23
706c771,781
< bad 35
---
> ok 25
> ok 26
> ok 27
> ok 28
> ok 29
> ok 30
> ok 31
> ok 32
> ok 33
> ok 34
> ok 35
708,709c783,784
< bad 37
< bad 38
---
> ok 37
> ok 38
run-dynvar
run-errors
8c8
< ./errors.tests: line 40: `1': not a valid identifier
---
> ./errors.tests: line 37: `1': not a valid identifier
16d15
< after posix select
18d16
< after posix select 2
26a25
> ./errors.tests: line 90: declare: -i: invalid option
30c29
< declare: usage: declare [-aAfFgiIlnrtux] [-p] [name[=value] ...]
---
> declare: usage: declare [-aAfFgiIlnrtux] [name[=value] ...] or declare -p [-aAfFilnrtux] [name ...]
54,55c53,54
< ./errors.tests: line 178: shift: --: shift count out of range
< ./errors.tests: line 179: shift: --: shift count out of range
---
> ./errors.tests: line 178: shift: 5: shift count out of range
> ./errors.tests: line 179: shift: -2: shift count out of range
70,73c69,72
< comsub: command substitution: line 2: syntax error near unexpected token `)'
< comsub: command substitution: line 2: ` for z in 1 2 3; do )'
< comsub: command substitution: line 2: syntax error near unexpected token `done'
< comsub: command substitution: line 2: ` for z in 1 2 3; done )'
---
> comsub: -c: line 1: syntax error near unexpected token `)'
> comsub: -c: line 1: `: $( for z in 1 2 3; do )'
> comsub: -c: line 1: syntax error near unexpected token `done' while looking for matching `)'
> comsub: -c: line 1: `: $( for z in 1 2 3; done )'
85c84
< .: usage: . filename [arguments]
---
> .: usage: . [-p path] filename [arguments]
87c86
< source: usage: source filename [arguments]
---
> source: usage: source [-p path] filename [arguments]
89c88
< .: usage: . filename [arguments]
---
> .: usage: . [-p path] filename [arguments]
91c90
< set: usage: set [-abefhkmnptuvxBCHP] [-o option-name] [--] [arg ...]
---
> set: usage: set [-abefhkmnptuvxBCEHPT] [-o option-name] [--] [-] [arg ...]
96c95
< read: usage: read [-ers] [-a array] [-d delim] [-i text] [-n nchars] [-N nchars] [-p prompt] [-t timeout] [-u fd] [name ...]
---
> read: usage: read [-Eers] [-a array] [-d delim] [-i text] [-n nchars] [-N nchars] [-p prompt] [-t timeout] [-u fd] [name ...]
114,115c113,114
< ./errors.tests: line 286: /bin/sh + 0: syntax error: operand expected (error token is "/bin/sh + 0")
< ./errors.tests: line 287: /bin/sh + 0: syntax error: operand expected (error token is "/bin/sh + 0")
---
> ./errors.tests: line 286: /bin/sh + 0: arithmetic syntax error: operand expected (error token is "/bin/sh + 0")
> ./errors.tests: line 287: /bin/sh + 0: arithmetic syntax error: operand expected (error token is "/bin/sh + 0")
118c117
< trap: usage: trap [-lp] [[arg] signal_spec ...]
---
> trap: usage: trap [-Plp] [[action] signal_spec ...]
134c133
< ./errors.tests: line 336: kill: @12: arguments must be process or job IDs
---
> ./errors.tests: line 336: kill: `@12': not a pid or valid job spec
139c138
< set: usage: set [-abefhkmnptuvxBCHP] [-o option-name] [--] [arg ...]
---
> set: usage: set [-abefhkmnptuvxBCEHPT] [-o option-name] [--] [-] [arg ...]
141c140
< set: usage: set [-abefhkmnptuvxBCHP] [-o option-name] [--] [arg ...]
---
> set: usage: set [-abefhkmnptuvxBCEHPT] [-o option-name] [--] [-] [arg ...]
145c144
< .: usage: . filename [arguments]
---
> .: usage: . [-p path] filename [arguments]
147c146
< ./errors1.sub: line 23: shift: --: shift count out of range
---
> ./errors1.sub: line 23: shift: -4: shift count out of range
150,151c149,150
< ./errors1.sub: line 29: break: --: loop count out of range
< ./errors1.sub: line 30: continue: --: loop count out of range
---
> ./errors1.sub: line 29: break: -5: loop count out of range
> ./errors1.sub: line 30: continue: -5: loop count out of range
162,164c161,163
< ./errors4.sub: line 24: var: readonly variable
< ./errors4.sub: line 28: f: readonly variable
< ./errors4.sub: line 31: var: readonly variable
---
> ./errors4.sub: line 27: var: readonly variable
> ./errors4.sub: line 31: f: readonly variable
> ./errors4.sub: line 34: var: readonly variable
168c167
< #? ./errors4.sub: line 34: var: readonly variable
---
> #? ./errors4.sub: line 37: var: readonly variable
172,173c171,172
< #? ./errors4.sub: line 37: var: readonly variable
< ./errors4.sub: line 42: break: x: numeric argument required
---
> #? ./errors4.sub: line 40: var: readonly variable
> ./errors4.sub: line 45: break: x: numeric argument required
237,238c236
< ./errors7.sub: line 21: notthere: command not found
< after no such command: 127
---
> after no such command: 1
240,241c238
< echo builtin
< after non-special builtin: 0
---
> after non-special builtin: 1
246c243
< ./errors8.sub: eval: line 7: syntax error: unexpected end of file
---
> ./errors8.sub: eval: line 7: syntax error: unexpected end of file from `(' command on line 6
261c258
< .: usage: . filename [arguments]
---
> .: usage: . [-p path] filename [arguments]
264c261
< ./errors9.sub: line 6: ++: syntax error: operand expected (error token is "+")
---
> ./errors9.sub: line 6: [[: ++: arithmetic syntax error: operand expected (error token is "+")
266c263
< ./errors9.sub: line 8: -- : syntax error: operand expected (error token is "- ")
---
> ./errors9.sub: line 8: ((: -- : arithmetic syntax error: operand expected (error token is "- ")
268c265
< ./errors9.sub: line 10: -- : syntax error: operand expected (error token is "- ")
---
> ./errors9.sub: line 10: ((: -- : arithmetic syntax error: operand expected (error token is "- ")
270a268
> after exit: 2
274,275c272,273
< after shift: 1
< environment: line 1: return: abcde: numeric argument required
---
> after shift: 2
> bash: line 1: return: abcde: numeric argument required
281,283c279
< after shift: 1
< environment: line 1: return: abcde: numeric argument required
< after return: 2
---
> bash: line 1: return: abcde: numeric argument required
285c281
< after history: 1
---
> after history: 2
287c283
< after history: 1
---
> after history: 2
290c286
< after exit: 45
---
> after exit: 2
292c288
< after return: 45
---
> after return: 2
294c290
< after shift: 45
---
> after shift: 2
296c292
< after break: 45
---
> after break: 2
298c294
< after continue: 45
---
> after continue: 2
300c296
< after exit: 45
---
> after exit: 2
302c298
< after return: 45
---
> after return: 2
304c300
< after shift: 45
---
> after shift: 2
306c302
< after break: 45
---
> after break: 2
308c304
< after continue: 45
---
> after continue: 2
320d315
< after: 1
322d316
< after: 1
324,325d317
< sh: line 1: readonly: `invalid+ident': not a valid identifier
< after: 1
327,328d318
< sh: line 1: export: `invalid+ident': not a valid identifier
< after: 1
342d331
< array: 1
344,349c333,337
< array: 1
< bash: -c: line 5: syntax error: unexpected end of file
< bash: -c: line 3: syntax error: unexpected end of file
< bash: -c: line 4: syntax error: unexpected end of file
< bash: -c: line 5: syntax error: unexpected end of file
< bash: -c: line 7: syntax error: unexpected end of file
---
> bash: -c: line 5: syntax error: unexpected end of file from `if' command on line 1
> bash: -c: line 3: syntax error: unexpected end of file from `while' command on line 1
> bash: -c: line 4: syntax error: unexpected end of file from `until' command on line 1
> bash: -c: line 5: syntax error: unexpected end of file from `for' command on line 1
> bash: -c: line 7: syntax error: unexpected end of file from `case' command on line 1
354d341
< after unset 1
356d342
< after unset 2
360c346
< ./errors.tests: line 394: `!!': not a valid identifier
---
> end
run-execscript
11c11
< bash: notthere: No such file or directory
---
> /tmp/bash: notthere: No such file or directory
28c28,39
< cp: cannot stat 'bash': No such file or directory
---
> trap -- 'echo EXIT' EXIT
> trap -- '' SIGTERM
> trap -- 'echo USR1' SIGUSR1
> USR1
> ./exec3.sub: line 38: /tmp/bash-notthere: No such file or directory
> ./exec3.sub: ENOENT: after failed exec: 127
> ./exec3.sub: line 43: exec: bash-notthere: not found
> trap -- 'echo EXIT' EXIT
> trap -- '' SIGTERM
> trap -- 'echo USR1' SIGUSR1
> USR1
> EXIT
35c46
< ./execscript: line 113: notthere: No such file or directory
---
> ./execscript: line 113: notthere: command not found
37c48
< ./execscript: line 115: notthere: No such file or directory
---
> ./execscript: line 115: notthere: command not found
44,45c55,57
< ./execscript: line 130: bash: No such file or directory
< ./execscript: line 132: bash: No such file or directory
---
> ok
> 5
> ./exec5.sub: line 4: exec: bash-notthere: not found
47,55c59,110
< ./execscript: line 135: bash: No such file or directory
< ./execscript: line 138: bash: No such file or directory
< ./execscript: line 141: bash: No such file or directory
< ./execscript: line 146: bash: No such file or directory
< ./execscript: line 149: bash: No such file or directory
< ./execscript: line 151: bash: No such file or directory
< ./execscript: line 153: bash: No such file or directory
< ./execscript: line 155: bash: No such file or directory
< ./execscript: line 156: bash: No such file or directory
---
> this is ohio-state
> 0
> 1
> 1
> 0
> 42
> 42
> 0
> 1
> 1
> 0
> 0
> 1
> 0
> 1
> 1 hi 1
> 2 hi 0
> !
> !
> 0
> 1
> 0
> testb
> expand_aliases      	on
> 1
> 1
> 1
> 1
> 0
> 0
> 0
> 0
> /usr/local/bin:/usr/GNU/bin:/usr/bin:/bin:.
> cannot find cat in $TMPDIR
> cannot find cat with empty $PATH
> PATH = /usr/local/bin:/usr/GNU/bin:/usr/bin:/bin:.
> cannot find cat in $TMPDIR with hash
> cannot find cat with empty $PATH with hash
> PATH = /usr/local/bin:/usr/GNU/bin:/usr/bin:/bin:.
> trap -- 'echo foo $BASH_SUBSHELL' EXIT
> trap -- 'echo USR1 $BASHPID' SIGUSR1
> between
> trap -- 'echo foo $BASH_SUBSHELL' EXIT
> trap -- 'echo USR1 $BASHPID' SIGUSR1
> between 2
> trap -- 'echo foo $BASH_SUBSHELL' EXIT
> trap -- 'echo USR1 $BASHPID' SIGUSR1
> in subshell: 1
> in subshell pipeline: 1
> group pipeline: 1
> EXIT-group.1
> foo 0
57,72c112,271
< ./execscript: line 163: bash: No such file or directory
< ./execscript: line 183: bash: No such file or directory
< ./execscript: line 184: bash: No such file or directory
< ./execscript: line 185: bash: No such file or directory
< ./execscript: line 187: bash: No such file or directory
< ./execscript: line 188: bash: No such file or directory
< ./execscript: line 189: bash: No such file or directory
< ./execscript: line 193: bash: No such file or directory
< ./execscript: line 194: bash: No such file or directory
< ./execscript: line 196: bash: No such file or directory
< ./execscript: line 197: bash: No such file or directory
< ./execscript: line 199: bash: No such file or directory
< ./execscript: line 200: bash: No such file or directory
< ./execscript: line 203: bash: No such file or directory
< ./execscript: line 206: bash: No such file or directory
< ./execscript: line 209: bash: No such file or directory
---
> exit code: 1
> exit code: 1
> exit code: 1
> exit code: 1
> exit code: 1
> exit code: 1
> a
> b
> c
> A
> B
> c
> d
> c
> d
> e
> x1
> x1a
> x2
> x2a
> x2b
> x3
> x3a
> x3b
> WORKS
> done
> WORKS
> WORKS
> a
> b
> c
> d
> a
> b
> c
> d
> e
> A
> B
> c
> d
> c
> d
> e
> x
> y
> z
> WORKS
> w
> x
> y
> z
> =====
> WORKS
> done
> WORKS
> a
> b
> c
> d
> a
> b
> c
> d
> e
> A
> B
> c
> d
> c
> d
> e
> x
> y
> z
> WORKS
> w
> x
> y
> z
> Darwin
> x
> archive
> install
> s
> sub1
> sub2
> test
> 68
> archive
> install
> s
> sub1
> sub2
> test
> 44
> archive
> install
> s
> sub1
> sub2
> test
> 86
> 2
> 78
> 1 start
> 2 start
> sub3
> 1 done
> 42
> test invert
> reached subshell
> reached group
> reached async group
> reached timed group
> reached simple
> reached if test
> reached if body
> reached while test
> reached while body
> reached until test
> reached until body
> reached func
> reached for
> reached arith for
> 1) a
> 2) b
> 3) c
> #? reached select
> reached case
> reached arith
> reached cond
> reached coproc body
> reached pipeline element invert
> reached AND-AND body
> reached OR-OR body
> reached AND-AND group
> reached OR-OR group
> ./exec17.sub: line 26: exec: notthere: not found
> after failed exec: 127
> ./exec17.sub: line 31: exec: notthere: not found
> after failed exec with output redirection
> ./exec17.sub: line 36: exec: notthere: not found
> ./exec17.sub: line 37: 4: Bad file descriptor
> ./exec17.sub: line 40: .: Is a directory
> after failed redir stdout
> after failed redir stderr
> ./exec17.sub: line 44: exec: notthere: not found
> after failed exec with input redirection
> ./exec17.sub: line 50: exec: notthere: not found
> after failed exec: 127
> ./exec17.sub: line 55: exec: notthere: not found
> after failed exec with output redirection
> ./exec17.sub: line 60: exec: notthere: not found
> ./exec17.sub: line 61: 4: Bad file descriptor
> ./exec17.sub: line 64: .: Is a directory
> after failed redir stdout
> after failed redir stderr
> ./exec17.sub: line 68: exec: notthere: not found
> after failed exec with input redirection
run-exp-tests
1,114c1,152
< ./exp.tests: line 35: recho: command not found
< ./exp.tests: line 37: recho: command not found
< ./exp.tests: line 39: recho: command not found
< ./exp.tests: line 41: recho: command not found
< ./exp.tests: line 43: recho: command not found
< ./exp.tests: line 45: recho: command not found
< ./exp.tests: line 48: recho: command not found
< ./exp.tests: line 50: recho: command not found
< ./exp.tests: line 52: recho: command not found
< ./exp.tests: line 55: recho: command not found
< ./exp.tests: line 57: recho: command not found
< ./exp.tests: line 61: recho: command not found
< ./exp.tests: line 63: recho: command not found
< ./exp.tests: line 65: recho: command not found
< ./exp.tests: line 67: recho: command not found
< ./exp.tests: line 69: recho: command not found
< ./exp.tests: line 71: recho: command not found
< ./exp.tests: line 75: recho: command not found
< ./exp.tests: line 77: recho: command not found
< ./exp.tests: line 79: recho: command not found
< ./exp.tests: line 83: recho: command not found
< ./exp.tests: line 85: recho: command not found
< ./exp.tests: line 87: recho: command not found
< ./exp.tests: line 89: recho: command not found
< ./exp.tests: line 91: recho: command not found
< ./exp.tests: line 93: recho: command not found
< ./exp.tests: line 100: recho: command not found
< ./exp.tests: line 102: recho: command not found
< ./exp.tests: line 104: recho: command not found
< ./exp.tests: line 106: recho: command not found
< ./exp.tests: line 108: recho: command not found
< ./exp.tests: line 110: recho: command not found
< ./exp.tests: line 116: recho: command not found
< ./exp.tests: line 118: recho: command not found
< ./exp.tests: line 120: recho: command not found
< ./exp.tests: line 122: recho: command not found
< ./exp.tests: line 124: recho: command not found
< ./exp.tests: line 126: recho: command not found
< ./exp.tests: line 130: recho: command not found
< ./exp.tests: line 132: recho: command not found
< ./exp.tests: line 135: recho: command not found
< ./exp.tests: line 139: recho: command not found
< ./exp.tests: line 141: recho: command not found
< ./exp.tests: line 146: recho: command not found
< ./exp.tests: line 150: recho: command not found
< ./exp.tests: line 152: recho: command not found
< ./exp.tests: line 154: recho: command not found
< ./exp.tests: line 157: recho: command not found
< ./exp.tests: line 160: recho: command not found
< ./exp.tests: line 165: recho: command not found
< ./exp.tests: line 170: recho: command not found
< ./exp.tests: line 174: recho: command not found
< ./exp.tests: line 177: recho: command not found
< ./exp.tests: line 182: recho: command not found
< ./exp.tests: line 184: recho: command not found
< ./exp.tests: line 186: recho: command not found
< ./exp.tests: line 188: recho: command not found
< ./exp.tests: line 193: recho: command not found
< ./exp.tests: line 195: recho: command not found
< ./exp.tests: line 199: recho: command not found
< ./exp.tests: line 203: recho: command not found
< ./exp.tests: line 205: recho: command not found
< ./exp.tests: line 207: recho: command not found
< ./exp.tests: line 210: recho: command not found
< ./exp.tests: line 212: recho: command not found
< ./exp.tests: line 217: recho: command not found
< ./exp.tests: line 222: recho: command not found
< ./exp.tests: line 224: recho: command not found
< ./exp.tests: line 228: recho: command not found
< ./exp.tests: line 230: recho: command not found
< ./exp.tests: line 234: recho: command not found
< ./exp.tests: line 238: recho: command not found
< ./exp.tests: line 244: recho: command not found
< ./exp.tests: line 247: recho: command not found
< ./exp.tests: line 252: recho: command not found
< ./exp.tests: line 257: recho: command not found
< ./exp.tests: line 262: recho: command not found
< ./exp.tests: line 267: recho: command not found
< ./exp.tests: line 273: recho: command not found
< ./exp.tests: line 275: recho: command not found
< ./exp.tests: line 278: recho: command not found
< ./exp.tests: line 280: recho: command not found
< ./exp.tests: line 285: recho: command not found
< ./exp.tests: line 288: recho: command not found
< ./exp.tests: line 291: recho: command not found
< ./exp.tests: line 298: recho: command not found
< ./exp.tests: line 301: recho: command not found
< ./exp.tests: line 308: recho: command not found
< ./exp.tests: line 313: recho: command not found
< ./exp.tests: line 316: recho: command not found
< ./exp.tests: line 319: recho: command not found
< ./exp.tests: line 325: recho: command not found
< ./exp.tests: line 331: recho: command not found
< ./exp.tests: line 338: recho: command not found
< ./exp.tests: line 341: recho: command not found
< ./exp.tests: line 352: recho: command not found
< ./exp.tests: line 357: recho: command not found
< ./exp.tests: line 362: recho: command not found
< ./exp.tests: line 367: recho: command not found
< ./exp.tests: line 372: recho: command not found
< ./exp.tests: line 374: recho: command not found
< ./exp.tests: line 376: recho: command not found
< ./exp.tests: line 378: recho: command not found
< ./exp.tests: line 380: recho: command not found
< ./exp.tests: line 382: recho: command not found
< ./exp.tests: line 384: recho: command not found
< ./exp.tests: line 386: recho: command not found
< ./exp.tests: line 389: recho: command not found
< ./exp.tests: line 391: recho: command not found
< ./exp.tests: line 394: recho: command not found
< ./exp.tests: line 397: recho: command not found
< ./exp.tests: line 400: recho: command not found
< ./exp.tests: line 402: recho: command not found
< ./exp.tests: line 408: recho: command not found
---
> argv[1] = <^A>
> argv[1] = <^A>
> argv[1] = <^?>
> argv[1] = <^?>
> argv[1] = <^A>
> argv[1] = <^?>
> argv[1] = <bar>
> argv[1] = <^A>
> argv[1] = <^?>
> argv[1] = <^A>
> argv[1] = <^?>
> argv[1] = <abcdefgh>
> argv[1] = <abcdefgh>
> argv[1] = <abcdefgh>
> argv[1] = <abcdefgh>
> argv[1] = <abcd>
> argv[1] = <abcd>
> argv[1] = < >
> argv[1] = <-->
> argv[1] = <>
> argv[1] = <>
> argv[1] = <>
> argv[1] = <>
> argv[1] = <>
> argv[1] = <>
> argv[1] = <abc>
> argv[1] = <abc>
> argv[1] = <abc>
> argv[1] = <abc>
> argv[1] = <abcdef>
> argv[1] = <abcdef>
> argv[1] = <^A>
> argv[1] = <^?>
> argv[1] = <^A>
> argv[1] = <^?>
> argv[1] = <^A>
> argv[1] = <^?>
> argv[1] = <>
> argv[1] = <>
> argv[1] = <>
> argv[1] = <Hello world!>
> argv[1] = <`>
> argv[1] = <">
> argv[1] = <\^A>
> argv[1] = <\$>
> argv[1] = <\\>
> argv[1] = <a>
> argv[2] = <b>
> argv[1] = <^A>
> argv[2] = <^?>
> argv[1] = <**>
> argv[1] = <\.\./*/>
> argv[1] = <^A^?^A^?>
> argv[1] = <^A^A>
> argv[1] = <^A^?>
> argv[1] = <^A^A^?>
> argv[1] = <  abc>
> argv[2] = <def>
> argv[3] = <ghi>
> argv[4] = <jkl  >
> argv[1] = <  abc>
> argv[2] = <def>
> argv[3] = <ghi>
> argv[4] = <jkl  >
> argv[1] = <--abc>
> argv[2] = <def>
> argv[3] = <ghi>
> argv[4] = <jkl-->
> argv[1] = <a b>
> argv[2] = <cd>
> argv[3] = <ef>
> argv[4] = <gh>
> argv[1] = <a b>
> argv[2] = <cd>
> argv[3] = <ef>
> argv[4] = <gh>
> argv[1] = <a b>
> argv[2] = <cd>
> argv[3] = <ef>
> argv[4] = <gh>
> argv[1] = <  >
> argv[1] = < - >
> argv[1] = </^root:/{s/^[^:]*:[^:]*:\([^:]*\).*$/\1/>
> argv[1] = <foo bar>
> argv[1] = <foo>
> argv[2] = <bar>
> argv[1] = <abc>
> argv[1] = <abc>
> argv[1] = <posix>
> argv[1] = <10>
> argv[1] = <5>
> argv[1] = <5>
> argv[1] = <file.o>
> argv[1] = <posix>
> argv[1] = </src/cmd>
> argv[1] = <three>
> argv[1] = <abcdef>
> argv[1] = <abcdef>
> argv[1] = <abcdef>
> argv[1] = <abcdef>
> argv[1] = <\$x>
> argv[1] = <$x>
> argv[1] = <\$x>
> argv[1] = <abc>
> argv[2] = <def>
> argv[3] = <ghi>
> argv[4] = <jkl>
> argv[1] = <abc def ghi jkl>
> argv[1] = <abc:def ghi:jkl>
> argv[1] = <abc>
> argv[2] = <def ghi>
> argv[3] = <jkl>
> argv[1] = <xxabc>
> argv[2] = <def ghi>
> argv[3] = <jklyy>
> argv[1] = <abc>
> argv[2] = <def ghi>
> argv[3] = <jklabc>
> argv[4] = <def ghi>
> argv[5] = <jkl>
> argv[1] = <abcdef>
> argv[1] = <bar>
> argv[2] = <>
> argv[3] = <xyz>
> argv[4] = <>
> argv[5] = <abc>
> argv[1] = <$foo>
> argv[1] = <10>
> argv[1] = <newline expected>
> argv[1] = <got it>
> argv[1] = <got it>
> argv[1] = <one>
> argv[2] = <three>
> argv[3] = <five>
> argv[1] = <5>
> argv[2] = <5>
> argv[1] = <3>
> argv[1] = <1>
> argv[1] = <1>
> argv[1] = <5>
> argv[1] = <5>
> argv[1] = <5>
> argv[1] = <5>
> argv[1] = <42>
> argv[1] = <26>
> argv[1] = <\>
> argv[1] = <~>
> argv[1] = <a>
> argv[2] = <b>
> argv[3] = <c>
> argv[4] = <d>
> argv[5] = <e>
117,141c155,182
< bash: line 1: recho: command not found
< ./exp1.sub: line 17: recho: command not found
< ./exp1.sub: line 18: recho: command not found
< ./exp1.sub: line 19: recho: command not found
< ./exp1.sub: line 22: recho: command not found
< ./exp1.sub: line 23: recho: command not found
< ./exp1.sub: line 24: recho: command not found
< ./exp1.sub: line 28: recho: command not found
< ./exp1.sub: line 32: recho: command not found
< ./exp1.sub: line 33: recho: command not found
< ./exp1.sub: line 34: recho: command not found
< ./exp1.sub: line 38: bad substitution: no closing `}' in "${_+\}"
< ./exp1.sub: line 39: bad substitution: no closing `}' in ${_+\}
< ./exp1.sub: line 40: recho: command not found
< ./exp1.sub: line 41: recho: command not found
< ./exp1.sub: line 42: recho: command not found
< ./exp1.sub: line 43: recho: command not found
< ./exp1.sub: line 44: recho: command not found
< ./exp1.sub: line 45: recho: command not found
< ./exp1.sub: line 47: recho: command not found
< ./exp1.sub: line 48: recho: command not found
< ./exp1.sub: line 50: recho: command not found
< ./exp1.sub: line 51: recho: command not found
< ./exp1.sub: line 53: recho: command not found
< ./exp1.sub: line 54: recho: command not found
---
> argv[1] = <a>
> argv[2] = <b>
> argv[3] = <>
> argv[1] = <^?>
> argv[1] = <^?>
> argv[1] = <^?>
> argv[1] = <^?>
> argv[1] = <^?>
> argv[1] = <^?>
> argv[1] = <^A>
> argv[2] = <^?>
> argv[1] = <^A^?>
> argv[1] = <^A^?^A^?>
> argv[1] = <^A^A^?>
> argv[1] = <\^A>
> argv[1] = <^A>
> argv[1] = <\^A>
> argv[1] = <\^A>
> argv[1] = <^A>
> argv[1] = <^A>
> argv[1] = <^A^A>
> argv[1] = <^A^A>
> argv[1] = <\^A>
> argv[1] = <\^A>
> argv[1] = <\^A^?>
> argv[1] = <\^A^?>
> argv[1] = <^\^A ^\^?>
> argv[1] = <^A ^_>
164,193c205,249
< ./exp6.sub: line 14: recho: command not found
< ./exp6.sub: line 15: recho: command not found
< ./exp6.sub: line 17: recho: command not found
< ./exp6.sub: line 19: recho: command not found
< ./exp6.sub: line 20: recho: command not found
< ./exp6.sub: line 22: recho: command not found
< ./exp6.sub: line 23: recho: command not found
< ./exp6.sub: line 25: recho: command not found
< ./exp6.sub: line 26: recho: command not found
< ./exp6.sub: line 28: recho: command not found
< ./exp6.sub: line 29: recho: command not found
< ./exp6.sub: line 36: recho: command not found
< ./exp6.sub: line 37: recho: command not found
< ./exp6.sub: line 38: recho: command not found
< ./exp6.sub: line 39: recho: command not found
< ./exp6.sub: line 40: recho: command not found
< ./exp6.sub: line 41: recho: command not found
< ./exp6.sub: line 42: recho: command not found
< ./exp6.sub: line 43: recho: command not found
< ./exp7.sub: line 19: recho: command not found
< ./exp7.sub: line 21: recho: command not found
< ./exp7.sub: line 24: recho: command not found
< ./exp7.sub: line 31: recho: command not found
< ./exp7.sub: line 32: recho: command not found
< ./exp7.sub: line 35: recho: command not found
< ./exp7.sub: line 36: recho: command not found
< ./exp8.sub: line 16: recho: command not found
< ./exp8.sub: line 17: recho: command not found
< declare -- var="xyz"
< ./exp8.sub: line 20: recho: command not found
---
> argv[1] = <a>
> argv[1] = <a>
> argv[1] = <^?>
> argv[1] = <^?b>
> argv[1] = <b^?>
> argv[1] = <c>
> argv[1] = <c>
> argv[1] = <c>
> argv[1] = <c>
> argv[1] = <c>
> argv[1] = <c>
> argv[1] = <correct>
> argv[2] = <>
> argv[1] = <correct>
> argv[2] = <>
> argv[1] = <correct>
> argv[2] = <>
> argv[1] = <XwrongX>
> argv[2] = <>
> argv[1] = <correct>
> argv[2] = <a>
> argv[1] = <XwrongX>
> argv[2] = <a>
> argv[1] = <correct>
> argv[2] = <a>
> argv[1] = <correct>
> argv[2] = <a>
> argv[1] = <^A>
> argv[1] = <3>
> argv[2] = <^C>
> argv[3] = <^C>
> argv[4] = <^C>
> argv[1] = <^A>
> argv[1] = <XY>
> argv[2] = <YX>
> argv[1] = <XY^AYX>
> argv[1] = <XY>
> argv[2] = <Y>
> argv[1] = <XY^AY>
> argv[1] = <x^Ay^?z>
> argv[1] = <x^Ay^?z>
> declare -- var=$'x\001y\177z'
> argv[1] = <declare>
> argv[2] = <-->
> argv[3] = <var=$'x\001y\177z'>
196,197c252,253
< ./exp8.sub: line 25: recho: command not found
< ./exp8.sub: line 26: recho: command not found
---
> argv[1] = <$'x\001y\177z'>
> argv[1] = <x^Ay^?z>
199c255
< ./exp8.sub: line 30: xyz: syntax error: invalid arithmetic operator (error token is "z")
---
> ./exp8.sub: line 30: xyz: arithmetic syntax error: invalid arithmetic operator (error token is "z")
202c258
< ./exp8.sub: line 39: recho: command not found
---
> argv[1] = <x^Ay^?z>
318,340c374,405
< ./exp11.sub: line 17: recho: command not found
< ./exp11.sub: line 20: recho: command not found
< ./exp11.sub: line 23: recho: command not found
< ./exp11.sub: line 24: recho: command not found
< ./exp11.sub: line 28: recho: command not found
< ./exp11.sub: line 30: recho: command not found
< ./exp11.sub: line 31: recho: command not found
< ./exp11.sub: line 37: recho: command not found
< ./exp11.sub: line 38: recho: command not found
< ./exp11.sub: line 39: recho: command not found
< ./exp11.sub: line 40: recho: command not found
< ./exp11.sub: line 41: recho: command not found
< ./exp11.sub: line 42: recho: command not found
< ./exp11.sub: line 43: recho: command not found
< ./exp11.sub: line 54: recho: command not found
< ./exp11.sub: line 58: recho: command not found
< ./exp11.sub: line 62: recho: command not found
< ./exp11.sub: line 66: recho: command not found
< ./exp11.sub: line 69: recho: command not found
< ./exp11.sub: line 79: recho: command not found
< ./exp11.sub: line 81: recho: command not found
< ./exp11.sub: line 85: recho: command not found
< ./exp11.sub: line 87: recho: command not found
---
> argv[1] = <1>
> argv[2] = <2>
> argv[1] = <1>
> argv[2] = <2>
> argv[1] = <1>
> argv[2] = <2>
> argv[1] = <1 2>
> argv[1] = <a b>
> argv[1] = <a>
> argv[2] = <b>
> argv[1] = <a b>
> argv[1] = <1>
> argv[2] = <2>
> argv[1] = <1>
> argv[2] = <2>
> argv[1] = <1>
> argv[2] = <2>
> argv[1] = <12>
> argv[1] = <12>
> argv[1] = <1>
> argv[2] = <2>
> argv[1] = <1>
> argv[2] = <2>
> argv[1] = < >
> argv[1] = < >
> argv[1] = < >
> argv[1] = < >
> argv[1] = < >
> argv[1] = <12>
> argv[1] = <12>
> argv[1] = <12>
> argv[1] = <12>
350,354c415,419
< ./exp12.sub: line 20: recho: command not found
< ./exp12.sub: line 24: recho: command not found
< ./exp12.sub: line 28: recho: command not found
< ./exp12.sub: line 32: recho: command not found
< ./exp12.sub: line 35: recho: command not found
---
> argv[1] = <file.o>
> argv[1] = <posix>
> argv[1] = </src/cmd>
> argv[1] = <three>
> argv[1] = </one/two/three>
365c430
< 4+3
---
> 7
369c434
< foo
---
> FOO
run-exportfunc
4c4
< ./exportfunc.tests: eval: line 44: syntax error: unexpected end of file
---
> ./exportfunc.tests: eval: line 44: syntax error: unexpected end of file from `{' command on line 42
8c8
< eval ok
---
> ./exportfunc.tests: eval: line 83: unexpected EOF while looking for matching `}'
run-extglob
80c80
< ./extglob.tests: line 371: recho: command not found
---
> argv[1] = <ef>
95,96c95,96
< . ..
< . .. a.log
---
> *(.)
> a.log
103,104c103,104
< . ..
< . ..
---
> *(foo).*
> *(foo|bar).*
117,127c117,126
< . .. .b a
< . .. .b a
< a .. .b
< . .. .b
< . .. .b
< .. .b a
< .. .b a
< a .. .b
< . .. .b
< . .. .b
< ./extglob7.sub: line 15: shopt: globskipdots: invalid shell option name
---
> .b a
> .b a
> a .b
> .b
> .b
> .b a
> .b a
> a .b
> .b
> .b
132c131
< . .. .a bar
---
> .a bar
134c133
< . .. .a .foo bar
---
> .a .foo bar
170c169
< . .. .a
---
> .. .a
186c185
< extglob        	off
---
> extglob             	off
188,192c187,191
< extglob        	off
< extglob        	off
< extglob        	off
< extglob        	off
< extglob        	off
---
> extglob             	off
> extglob             	off
> extglob             	off
> extglob             	off
> extglob             	off
run-extglob2
run-extglob3
run-func
174c174
< a=2 () 
---
> function a=2 () 
182c182
< a=2 () 
---
> function a=2 () 
195,200c195,196
< break is a function
< break () 
< { 
<     echo inside function $FUNCNAME
< }
< function
---
> break is a special shell builtin
> builtin
204,208c200
< break is a function
< break () 
< { 
<     echo inside function $FUNCNAME
< }
---
> break is a special shell builtin
209a202
> break is a special shell builtin
215d207
< break is a special shell builtin
253,254c245,254
< ./func5.sub: line 101: `!!': not a valid identifier
< ./func5.sub: line 105: `!!': not a valid identifier
---
> !! is a function
> !! () 
> { 
>     fc -s "$@"
> }
> !! is a function
> !! () 
> { 
>     fc -s "$@"
> }
run-getopts
run-glob-bracket
0a1,103
> --- $GLOBIGNORE vs fnmatch(3) ---
> #1: pat=ab/cd/efg        yes/yes
> #2: pat=ab[/]cd/efg      no/no
> #3: pat=ab[/a]cd/efg     no/no
> #4: pat=ab[a/]cd/efg     no/no
> #5: pat=ab[!a]cd/efg     no/no
> #6: pat=ab[.-0]cd/efg    no/no
> #7: pat=*/*/efg          yes/yes
> #8: pat=*[/]*/efg        no/no
> #9: pat=*[/a]*/efg       no/no
> #10: pat=*[a/]*/efg       no/no
> #11: pat=*[!a]*/efg       no/no
> #12: pat=*[.-0]*/efg      no/no
> #13: pat=*/*/efg          yes/yes
> #14: pat=*[b]/*/efg       yes/yes
> #15: pat=*[ab]/*/efg      yes/yes
> #16: pat=*[ba]/*/efg      yes/yes
> #17: pat=*[!a]/*/efg      yes/yes
> #18: pat=*[a-c]/*/efg     yes/yes
> #19: pat=ab@(/)cd/efg     yes/yes
> #20: pat=*@(/)cd/efg      no/no
> #21: pat=*/cd/efg         yes/yes
> 
> ---Tests for a slash in bracket expressions---
> #22: pat=ab[/]ef              str=ab[/]ef          yes/yes
> #23: pat=ab[/]ef              str=ab/ef            no/no
> #24: pat=ab[c/d]ef            str=ab[c/d]ef        yes/yes
> #25: pat=ab[c/d]ef            str=abcef            no/no
> #26: pat=ab[.-/]ef            str=ab[.-/]ef        yes/yes
> #27: pat=ab[.-/]ef            str=ab.ef            no/no
> #28: pat=ab[[=/=]]ef          str=ab[[=/=]]ef      yes/yes
> #29: pat=ab[[=/=]]ef          str=ab/ef            no/no
> #30: pat=ab[[=c=]/]ef         str=ab[=/]ef         yes/yes
> #31: pat=ab[[=c=]/]ef         str=abcef            no/no
> #32: pat=ab[[:alpha:]/]ef     str=ab[:/]ef         yes/yes
> #33: pat=ab[[:alpha:]/]ef     str=abxef            no/no
> #34: pat=ab[/[abc]]ef         str=ab[/c]ef         yes/yes
> #35: pat=ab[/[abc]]ef         str=abc]ef           no/no
> #36: pat=ab[c[=/=]]ef         str=ab[c[=/=]]ef     yes/yes
> #37: pat=ab[c[=/=]]ef         str=abc[=/=]ef       no/no
> #38: pat=ab[c[=/=]]ef         str=abcef            no/no
> #39: pat=a[b\/c]              str=a[b/c]           yes/yes
> #40: pat=a[b\/c]              str=ab               no/no
> #41: pat=a[b\/c]              str=ac               no/no
> 
> ---Tests for incomplete bracket expressions---
> #42: pat=ab[c                 str=ab[c             yes/yes
> #43: pat=ab[c                 str=abc              no/no
> #44: pat=ab[c[=d=             str=ab[c[=d=         yes/yes
> #45: pat=ab[c[=d=             str=abc              no/no
> #46: pat=ab[c[.d              str=ab[c[.d          yes/yes
> #47: pat=ab[c[.d              str=abc              no/no
> #48: pat=ab[c[:alpha:         str=ab[c[:alpha:     yes/yes
> #49: pat=ab[c[:alpha:         str=abc              no/no
> #50: pat=ab[c-                str=ab[c-            yes/yes
> #51: pat=ab[c-                str=abc              no/no
> #52: pat=ab[c\                str=ab[c\            yes/yes
> #53: pat=ab[c\                str=abc              no/no
> #54: pat=ab[[\                str=ab[[\            yes/yes
> #55: pat=ab[[\                str=ab[              no/no
> 
> --- PATSCAN vs BRACKMATCH ---
> #56: pat=@([[.].])A])         str=]                yes/yes
> #57: pat=@([[.].])A])         str===]A])           no/no
> #58: pat=@([[.].])A])         str=AA])             no/no
> #59: pat=@([[=]=])A])         str=]                no/no
> #60: pat=@([[=]=])A])         str===]A])           yes/yes
> #61: pat=@([[=]=])A])         str=AA])             no/no
> 
> --- BRACKMATCH: after match vs before match ---
> #62: pat=[[=]=]ab]            str=a                no/no
> #63: pat=[[.[=.]ab]           str=a                yes/yes
> #64: pat=[[.[==].]ab]         str=a                yes/yes
> 
> #65: pat=[a[=]=]b]            str=a                no/no
> #66: pat=[a[.[=.]b]           str=a                yes/yes
> #67: pat=[a[.[==].]b]         str=a                yes/yes
> 
> #68: pat=[a[=]=]b]            str=b                no/no
> #69: pat=[a[=]=]b]            str=a=]b]            yes/yes
> #70: pat=[a[.[=.]b]           str=b                yes/yes
> #71: pat=[a[.[=.]b]           str=ab]              no/no
> #72: pat=[a[.[==].]b]         str=b                yes/yes
> #73: pat=[a[.[==].]b]         str=ab]              no/no
> 
> --- incomplete POSIX brackets ---
> #74: pat=x[a[:y]              str=x[               yes/yes
> #75: pat=x[a[:y]              str=x:               yes/yes
> #76: pat=x[a[:y]              str=xy               yes/yes
> #77: pat=x[a[:y]              str=x[ay             no/no
> 
> #78: pat=x[a[.y]              str=x[               yes/yes
> #79: pat=x[a[.y]              str=x.               yes/yes
> #80: pat=x[a[.y]              str=xy               yes/yes
> #81: pat=x[a[.y]              str=x[ay             no/no
> 
> #82: pat=x[a[=y]              str=x[               yes/yes
> #83: pat=x[a[=y]              str=x=               yes/yes
> #84: pat=x[a[=y]              str=xy               yes/yes
> #85: pat=x[a[=y]              str=x[ay             no/no
> 
> --- MISC tests ---
> #86: pat=a\                   str=a\               yes/yes
run-glob-test
2,3d1
< glob2.sub: warning: you do not have the zh_TW.big5 locale installed;
< glob2.sub: warning: that may cause some of these tests to fail.
9d6
< ./glob2.sub: line 44: warning: setlocale: LC_ALL: cannot change locale (zh_TW.big5): No such file or directory
11,15c8,12
< ./glob2.sub: line 53: recho: command not found
< ./glob2.sub: line 55: recho: command not found
< ./glob2.sub: line 56: recho: command not found
< ./glob2.sub: line 59: recho: command not found
< 0000000 141 316 261 142
---
> argv[1] = <A£\B>
> argv[1] = <A>
> argv[1] = <B>
> argv[1] = <a£\b>
> 0000000 141 243 134 142
18,19d14
< ./glob2.sub: line 65: warning: setlocale: LC_ALL: cannot change locale (zh_TW.big5)
< bash: warning: setlocale: LC_ALL: cannot change locale (zh_TW.big5)
72c67
< ./glob4.sub: line 24: recho: command not found
---
> argv[1] = <a\?>
74c69
< ./glob4.sub: line 28: recho: command not found
---
> argv[1] = <a\?>
86,105c81,101
< ./glob5.sub: line 42: recho: command not found
< ./glob5.sub: line 43: recho: command not found
< ./glob5.sub: line 44: recho: command not found
< ./glob5.sub: line 46: recho: command not found
< ./glob5.sub: line 47: recho: command not found
< ./glob5.sub: line 48: recho: command not found
< ./glob5.sub: line 49: recho: command not found
< ./glob5.sub: line 50: recho: command not found
< ./glob5.sub: line 51: recho: command not found
< ./glob5.sub: line 52: recho: command not found
< ./glob5.sub: line 53: recho: command not found
< ./glob5.sub: line 55: recho: command not found
< ./glob5.sub: line 56: recho: command not found
< ./glob5.sub: line 58: recho: command not found
< ./glob5.sub: line 59: recho: command not found
< ./glob5.sub: line 60: recho: command not found
< ./glob5.sub: line 61: recho: command not found
< ./glob5.sub: line 63: recho: command not found
< ./glob5.sub: line 72: recho: command not found
< ./glob5.sub: line 73: recho: command not found
---
> argv[1] = <./tmp/a/*>
> argv[1] = <./tmp/a/*>
> argv[1] = <./tmp/a/b/c>
> argv[1] = <./tmp/a/*>
> argv[1] = <./tmp/a/b/c>
> argv[1] = <./t\mp/a/*>
> argv[1] = <./tmp/a/b/c>
> argv[1] = <./tmp/a/>
> argv[1] = <./tmp/a/b/>
> argv[1] = <./t\mp/a/>
> argv[1] = <./t\mp/a/b/>
> argv[1] = <./tmp/a/*>
> argv[1] = <./tmp/a/b/c>
> argv[1] = <./tmp/a>
> argv[1] = <./tmp/a/b*>
> argv[1] = <./tmp/a>
> argv[1] = <./tmp/a/b*>
> argv[1] = <./tmp/>
> argv[1] = <\$foo>
> argv[2] = <\$foo>
> argv[1] = <mixed\$foo/>
130,132c126
< ./glob10.sub: line 26: shopt: globskipdots: invalid shell option name
< . .. .a .aa .b .bb
< ./glob10.sub: line 28: shopt: globskipdots: invalid shell option name
---
> .a .aa .b .bb
137c131
< mailcheck.o make_cmd.o mksignames mksignames.o mksyntax mksyntax.dSYM
---
> mksyntax.dSYM mksyntax mksignames.o mksignames make_cmd.o mailcheck.o
142,143c136,137
< mailcheck.o make_cmd.o mksignames mksignames.o mksyntax mksyntax.dSYM
< mailcheck.o make_cmd.o mksignames mksignames.o mksyntax mksyntax.dSYM
---
> mksyntax mksignames make_cmd.o mailcheck.o mksignames.o mksyntax.dSYM
> mksyntax.dSYM mksignames.o mailcheck.o make_cmd.o mksignames mksyntax
145,146c139,140
< mailcheck.o make_cmd.o mksignames mksignames.o mksyntax mksyntax.dSYM
< mailcheck.o make_cmd.o mksignames mksignames.o mksyntax mksyntax.dSYM
---
> mksyntax mksignames make_cmd.o mailcheck.o mksignames.o mksyntax.dSYM
> mksyntax.dSYM mksignames.o mailcheck.o make_cmd.o mksignames mksyntax
148,150c142,143
< mailcheck.o make_cmd.o mksignames mksignames.o mksyntax mksyntax.dSYM
< mailcheck.o make_cmd.o mksignames mksignames.o mksyntax mksyntax.dSYM
< aa ab ac
---
> mksyntax mksignames make_cmd.o mailcheck.o mksignames.o mksyntax.dSYM
> mksyntax.dSYM mksignames.o mailcheck.o make_cmd.o mksignames mksyntax
152,154c145,158
< ./glob.tests: line 48: recho: command not found
< ./glob.tests: line 51: recho: command not found
< ./glob.tests: line 57: recho: command not found
---
> ac ab aa
> argv[1] = <a>
> argv[2] = <abc>
> argv[3] = <abd>
> argv[4] = <abe>
> argv[5] = <X*>
> argv[1] = <a>
> argv[2] = <abc>
> argv[3] = <abd>
> argv[4] = <abe>
> argv[1] = <a>
> argv[2] = <abc>
> argv[3] = <abd>
> argv[4] = <abe>
157,173c161,198
< ./glob.tests: line 73: recho: command not found
< ./glob.tests: line 77: recho: command not found
< ./glob.tests: line 80: recho: command not found
< ./glob.tests: line 83: recho: command not found
< ./glob.tests: line 86: recho: command not found
< ./glob.tests: line 89: recho: command not found
< ./glob.tests: line 92: recho: command not found
< ./glob.tests: line 95: recho: command not found
< ./glob.tests: line 98: recho: command not found
< ./glob.tests: line 102: recho: command not found
< ./glob.tests: line 107: recho: command not found
< ./glob.tests: line 110: recho: command not found
< ./glob.tests: line 113: recho: command not found
< ./glob.tests: line 117: recho: command not found
< ./glob.tests: line 121: recho: command not found
< ./glob.tests: line 129: recho: command not found
< ./glob.tests: line 132: recho: command not found
---
> argv[1] = <bdir/>
> argv[1] = <*>
> argv[1] = <a*>
> argv[1] = <a*>
> argv[1] = <c>
> argv[2] = <ca>
> argv[3] = <cb>
> argv[4] = <a*>
> argv[5] = <*q*>
> argv[1] = <**>
> argv[1] = <**>
> argv[1] = <\.\./*/>
> argv[1] = <s/\..*//>
> argv[1] = </^root:/{s/^[^:]*:[^:]*:\([^:]*\).*$/\1/>
> argv[1] = <abc>
> argv[2] = <abd>
> argv[3] = <abe>
> argv[4] = <bb>
> argv[5] = <cb>
> argv[1] = <abd>
> argv[2] = <abe>
> argv[3] = <bb>
> argv[4] = <bcd>
> argv[5] = <bdir>
> argv[6] = <ca>
> argv[7] = <cb>
> argv[8] = <dd>
> argv[9] = <de>
> argv[1] = <abd>
> argv[2] = <abe>
> argv[1] = <a-b>
> argv[2] = <aXb>
> argv[1] = <Beware>
> argv[2] = <d>
> argv[3] = <dd>
> argv[4] = <de>
> argv[1] = <a*b/ooo>
> argv[1] = <a*b/ooo>
176,179c201,204
< ./glob.tests: line 150: recho: command not found
< ./glob.tests: line 153: recho: command not found
< ./glob.tests: line 156: recho: command not found
< ./glob.tests: line 159: recho: command not found
---
> argv[1] = <abc>
> argv[1] = <abc>
> argv[1] = <abc>
> argv[1] = <abc>
187,189c212,214
< ./glob.tests: line 208: recho: command not found
< ./glob.tests: line 210: recho: command not found
< ./glob.tests: line 212: recho: command not found
---
> argv[1] = <man/man1/bash.1>
> argv[1] = <man/man1/bash.1>
> argv[1] = <man/man1/bash.1>
219,227c244,279
< ./glob.tests: line 372: recho: command not found
< ./glob.tests: line 375: recho: command not found
< ./glob.tests: line 377: recho: command not found
< ./glob.tests: line 382: recho: command not found
< ./glob.tests: line 387: recho: command not found
< ./glob.tests: line 390: recho: command not found
< ./glob.tests: line 394: recho: command not found
< ./glob.tests: line 398: recho: command not found
< ./glob.tests: line 403: recho: command not found
---
> argv[1] = <b>
> argv[2] = <bb>
> argv[3] = <bcd>
> argv[4] = <bdir>
> argv[1] = <Beware>
> argv[2] = <b>
> argv[3] = <bb>
> argv[4] = <bcd>
> argv[5] = <bdir>
> argv[1] = <Beware>
> argv[2] = <b>
> argv[3] = <bb>
> argv[4] = <bcd>
> argv[5] = <bdir>
> argv[1] = <*>
> argv[1] = <a*b>
> argv[2] = <a-b>
> argv[3] = <aXb>
> argv[4] = <abd>
> argv[5] = <bb>
> argv[6] = <bcd>
> argv[7] = <bdir>
> argv[8] = <ca>
> argv[9] = <cb>
> argv[10] = <dd>
> argv[11] = <man>
> argv[1] = <Beware>
> argv[2] = <abc>
> argv[3] = <abe>
> argv[4] = <bdir>
> argv[5] = <ca>
> argv[6] = <de>
> argv[7] = <man>
> argv[1] = <*>
> argv[1] = <man/man1/bash.1>
> argv[1] = <man/man1/bash.1>
run-globstar
run-heredoc
74c74
< ./heredoc3.sub: line 23: warning: here-document at line 21 delimited by end-of-file (wanted `EOF')
---
> ./heredoc3.sub: line 20: warning: here-document at line 18 delimited by end-of-file (wanted `EOF')
76c76
< ./heredoc3.sub: line 29: warning: here-document at line 27 delimited by end-of-file (wanted `EOF')
---
> ./heredoc3.sub: line 26: warning: here-document at line 24 delimited by end-of-file (wanted `EOF')
78c78
< ./heredoc3.sub: line 35: warning: here-document at line 33 delimited by end-of-file (wanted `EOF')
---
> ./heredoc3.sub: line 32: warning: here-document at line 30 delimited by end-of-file (wanted `EOF')
80c80
< ./heredoc3.sub: line 41: warning: here-document at line 39 delimited by end-of-file (wanted `EOF')
---
> ./heredoc3.sub: line 38: warning: here-document at line 36 delimited by end-of-file (wanted `EOF')
98c98
< ./heredoc3.sub: line 99: syntax error: unexpected end of file
---
> ./heredoc3.sub: line 99: syntax error: unexpected end of file from `(' command on line 96
102,112c102,109
< ./heredoc4.sub: line 11: recho: command not found
< ./heredoc4.sub: line 12: recho: command not found
< cat: ../y.tab.c: No such file or directory
< cmp: ../y.tab.c: No such file or directory
< cat: ../config.h: No such file or directory
< cmp: ../config.h: No such file or directory
< cat: ../version.h: No such file or directory
< cmp: ../version.h: No such file or directory
< 1: no	OK
< 2: Ono	OK
< 3: no	OK
---
> argv[1] = <onetwo>
> argv[2] = <threefour>
> argv[1] = <two>
> argv[2] = <threefi>
> argv[3] = <ve>
> 1: OK
> 2: OK
> 3: OK
115c112
< 6: notOK
---
> 6: OK
117,119c114,116
< 1: no	OK
< 2: no	OK
< 3: Ono	OK
---
> 1: OK
> 2: OK
> 3: OK
121c118
< 5: notOK
---
> 5: OK
130,135c127,128
< ./heredoc7.sub: line 18: warning: here-document at line 18 delimited by end-of-file (wanted `EOF')
< ./heredoc7.sub: line 17: warning: here-document at line 17 delimited by end-of-file (wanted `EOF')
< 
< ./heredoc7.sub: line 18: foo: command not found
< ./heredoc7.sub: line 19: bar: command not found
< ./heredoc7.sub: line 20: EOF: command not found
---
> ./heredoc7.sub: line 17: warning: command substitution: 1 unterminated here-document
> foo bar
138,139c131,132
< ./heredoc7.sub: line 30: foobar: command not found
< ./heredoc7.sub: line 31: EOF: command not found
---
> ./heredoc7.sub: line 26: foobar: command not found
> ./heredoc7.sub: line 27: EOF: command not found
144,145c137
<     if cat <<HERE; then
<         echo 1 2
---
>     if cat <<HERE
148c140,141
< 
---
>     then
>         echo 1 2;
158,159c151,152
<  do
<         echo 1 2
---
>     do
>         echo 1 2;
163,167c156,158
< 
< # here-document body continues after alias definition
< alias 'headplus=cat <<EOF
< hello'
< headplus
---
> hello
> world
> hello
169,172d159
< ./heredoc10.sub: line 30: hello: command not found
< ./heredoc10.sub: line 30: world: command not found
< ./heredoc10.sub: line 30: EOF: command not found
< ./heredoc10.sub: line 32: unalias: headplus: not found
175,178d161
< 
< # make sure delimiter is recognized whether the alias ends with a newline or not
< shopt -s expand_aliases
< alias head='cat <<\END' body='head
180,183c163
< ./heredoc10.sub: line 51: here-document: command not found
< ./heredoc10.sub: line 51: END: command not found
< ./heredoc10.sub: line 52: unexpected EOF while looking for matching `''
< ./heredoc10.sub: line 56: syntax error: unexpected end of file
---
> here-document
run-herestr
run-histexpand
139,141c139,253
< echo $((1+2)
< ./histexp.tests: line 151: unexpected EOF while looking for matching `)'
< ./histexp.tests: line 160: syntax error: unexpected end of file
---
> echo $((1+2))
> 3
> !
> !
> !
> !
> !
> !
> !
> !
> !
> \!
> \!
> \!
> \!
> 1 hi 1
> 2 hi 0
> !
> !
> a
> b
> c
> echo "#!/bin/bash" set -o posix
> #!/bin/bash set -o posix
> !!
> !!
> a
> echo $(echo echo a)
> echo a
> a
> echo echo a $(echo echo a)
> echo a echo a
> b
> !! $(echo !!)
> c
> echo "echo c" "$(echo echo c)"
> echo c echo c
> d
> echo "echo d" $(echo "echo d")
> echo d echo d
> e
> !! !!
> f
> !!
> f
> !!
> g
> echo "echo g"
> echo g
> g
> eval echo "echo g"
> echo g
> h
> echo \!\! `echo echo h`
> !! echo h
> i
> echo echo i `echo echo i`
> echo i echo i
> j
> echo `echo j` echo j
> j echo j
> a
> cat < <(echo echo a)
> echo a
> b
> echo echo b `echo echo b`
> echo b echo b
> c
> !
> d
> !
> e
> ! !
> ./histexp4.sub: line 33: !': event not found
> /tmp/Step1
> echo /$(echo tmp)/Step1
> /tmp/Step1
> echo /<(echo tmp)/Step1 > /dev/null
> /tmp/Step1
> echo $(echo /tmp)/Step1
> /tmp/Step1
> echo <(echo /tmp)/Step1 > /dev/null
> /+(one|two|three)/Step1
> echo /+(one|two|three)/Step1
> /+(one|two|three)/Step1
> /*(tmp|dev|usr)/Step1
> echo /*(tmp|dev|usr)/Step1
> /*(tmp|dev|usr)/Step1
> +(/one|/two|/three)/Step1
> echo +(/one|/two|/three)/Step1
> +(/one|/two|/three)/Step1
> *(/tmp|/dev|/usr)/Step1
> echo *(/tmp|/dev|/usr)/Step1
> *(/tmp|/dev|/usr)/Step1
> one
> 	echo echo one
> echo one
> echo one
> echo one
>     1  set -o histexpand
>     2  echo one
>     3  for f in a b c; do 	echo echo one; done
>     4  history
> two
> 	echo echo two
> echo two
> echo two
> echo two
>     1  echo two
>     2  for f in a b c; do 	echo echo two; done
>     3  history
> a
> echo !!
> --between--
> echo !!
run-history
145c145
< 5.1
---
> 5.3
147c147
< 5.1
---
> 5.3
183c183
< ./history3.sub: line 48: history: @42: history position out of range
---
> ./history3.sub: line 48: history: @42: invalid number
306d305
< ./history6.sub: line 40: history: -1: history position out of range
310d308
<     7  echo 7
313c311
< ./history6.sub: line 45: history: -2: history position out of range
---
>     5  echo 5
315,317d312
<     7  echo 7
<     8  echo 7
<     9  echo 8
320,328c315,319
<     8  echo 7
<     9  echo 8
<    10  echo 9
<    11  echo 10
< ./history6.sub: line 51: history: 5: history position out of range
<     8  echo 7
<     9  echo 8
<    10  echo 9
<    11  echo 10
---
>     5  echo 5
>     6  echo 6
>     7  echo 9
>     8  echo 10
>     5  echo 10
333c324
< 5
---
> 6
340c331
< 5
---
> 6
385a377,379
> 
> 
> 
386a381
> 
387a383
> 
391a388,389
> 
> 
395a394,395
> 
> 
run-ifs
11,12c11,12
< ./ifs1.sub: line 9: recho: command not found
< ./ifs1.sub: line 11: recho: command not found
---
> argv[1] = <file>
> argv[1] = <*>
run-ifs-posix
run-input-test
run-intl
13a14
> 1,0000
18,19c19
< 1.0000
< 1.0000
---
> 1,0000
24c24
< Passed all 1318 Unicode tests
---
> Passed all 1770 Unicode tests
60,63d59
< à
< à²
<   à²
< à²  ---
65,67c61,67
< à
<    à
< à   ---
---
> à²‡à²³
>   à²‡à²³
> à²‡à²³  ---
> à²‡
> à²‡
>    à²‡
> à²‡   ---
run-invert
run-invocation
4,5c4,5
< Usage:	bash [GNU long option] [option] ...
< 	bash [GNU long option] [option] script-file ...
---
> bash [GNU long option] [option] ...
> bash [GNU long option] [option] script-file ...
25c25
< 	-abefhkmnptuvxBCHP or -o option
---
> 	-abefhkmnptuvxBCEHPT or -o option
27,28c27,28
< Usage:	bash [GNU long option] [option] ...
< 	bash [GNU long option] [option] script-file ...
---
> bash [GNU long option] [option] ...
> bash [GNU long option] [option] script-file ...
48c48
< 	-abefhkmnptuvxBCHP or -o option
---
> 	-abefhkmnptuvxBCEHPT or -o option
50,51c50,51
< Usage:	bash [GNU long option] [option] ...
< 	bash [GNU long option] [option] script-file ...
---
> bash [GNU long option] [option] ...
> bash [GNU long option] [option] script-file ...
71c71
< 	-abefhkmnptuvxBCHP or -o option
---
> 	-abefhkmnptuvxBCEHPT or -o option
75,77c75,77
< checkwinsize:cmdhist:complete_fullquote:extquote:force_fignore:globasciiranges:hostcomplete:interactive_comments:progcomp:promptvars:sourcepath
< checkhash:checkwinsize:cmdhist:complete_fullquote:extquote:force_fignore:globasciiranges:hostcomplete:interactive_comments:progcomp:promptvars:sourcepath
< cmdhist:complete_fullquote:extquote:force_fignore:globasciiranges:hostcomplete:interactive_comments:progcomp:promptvars:sourcepath
---
> checkwinsize:cmdhist:complete_fullquote:extquote:force_fignore:globasciiranges:globskipdots:hostcomplete:interactive_comments:patsub_replacement:progcomp:promptvars:sourcepath
> checkhash:checkwinsize:cmdhist:complete_fullquote:extquote:force_fignore:globasciiranges:globskipdots:hostcomplete:interactive_comments:patsub_replacement:progcomp:promptvars:sourcepath
> cmdhist:complete_fullquote:extquote:force_fignore:globasciiranges:globskipdots:hostcomplete:interactive_comments:patsub_replacement:progcomp:promptvars:sourcepath
run-iquote
1,10c1,10
< ./iquote.tests: line 20: recho: command not found
< ./iquote.tests: line 23: recho: command not found
< ./iquote.tests: line 30: recho: command not found
< ./iquote.tests: line 33: recho: command not found
< ./iquote.tests: line 39: recho: command not found
< ./iquote.tests: line 39: recho: command not found
< ./iquote.tests: line 49: recho: command not found
< ./iquote.tests: line 52: recho: command not found
< ./iquote.tests: line 55: recho: command not found
< ./iquote.tests: line 58: recho: command not found
---
> argv[1] = <xxxyyy>
> argv[1] = <xxx^?yyy>
> argv[1] = <xy>
> argv[1] = <x^?y>
> argv[1] = <-->
> argv[1] = <-^?->
> argv[1] = <>
> argv[1] = <>
> argv[1] = <^?>
> argv[1] = <^?yy>
14,33c14,40
< ./iquote.tests: line 72: recho: command not found
< ./iquote.tests: line 73: recho: command not found
< ./iquote.tests: line 74: recho: command not found
< ./iquote.tests: line 75: recho: command not found
< ./iquote.tests: line 77: recho: command not found
< ./iquote.tests: line 78: recho: command not found
< ./iquote.tests: line 79: recho: command not found
< ./iquote.tests: line 80: recho: command not found
< ./iquote.tests: line 86: recho: command not found
< ./iquote.tests: line 86: recho: command not found
< ./iquote.tests: line 86: recho: command not found
< ./iquote.tests: line 86: recho: command not found
< ./iquote.tests: line 105: recho: command not found
< ./iquote.tests: line 106: recho: command not found
< ./iquote.tests: line 107: recho: command not found
< ./iquote.tests: line 108: recho: command not found
< ./iquote.tests: line 111: recho: command not found
< ./iquote.tests: line 112: recho: command not found
< ./iquote.tests: line 114: recho: command not found
< ./iquote.tests: line 115: recho: command not found
---
> argv[1] = <^?>
> argv[1] = <^?@>
> argv[1] = <@^?@>
> argv[1] = <@^?>
> argv[1] = <^?>
> argv[1] = <^?@>
> argv[1] = <@^?@>
> argv[1] = <@^?>
> argv[1] = <1>
> argv[2] = <^?>
> argv[3] = <^?>
> argv[1] = <2>
> argv[2] = <^?a>
> argv[3] = <^?a>
> argv[1] = <2>
> argv[2] = <^?a>
> argv[3] = <^?a>
> argv[1] = <3>
> argv[2] = <^?aa>
> argv[3] = <^?aa>
> argv[1] = <>
> argv[1] = <-->
> argv[1] = <-->
> argv[1] = <^?>
> argv[1] = <-^?->
> argv[1] = <^?>
> argv[1] = <-^?->
35,85c42,92
< ./iquote.tests: line 130: recho: command not found
< ./iquote.tests: line 131: recho: command not found
< ./iquote.tests: line 132: recho: command not found
< ./iquote.tests: line 133: recho: command not found
< ./iquote.tests: line 136: recho: command not found
< ./iquote.tests: line 137: recho: command not found
< ./iquote.tests: line 138: recho: command not found
< ./iquote.tests: line 139: recho: command not found
< ./iquote.tests: line 142: recho: command not found
< ./iquote.tests: line 143: recho: command not found
< ./iquote.tests: line 144: recho: command not found
< ./iquote.tests: line 145: recho: command not found
< ./iquote.tests: line 148: recho: command not found
< ./iquote.tests: line 149: recho: command not found
< ./iquote.tests: line 150: recho: command not found
< ./iquote.tests: line 151: recho: command not found
< ./iquote.tests: line 153: recho: command not found
< ./iquote.tests: line 154: recho: command not found
< ./iquote.tests: line 155: recho: command not found
< ./iquote.tests: line 156: recho: command not found
< ./iquote1.sub: line 22: recho: command not found
< ./iquote1.sub: line 23: recho: command not found
< ./iquote1.sub: line 24: recho: command not found
< ./iquote1.sub: line 25: recho: command not found
< ./iquote1.sub: line 27: recho: command not found
< ./iquote1.sub: line 28: recho: command not found
< ./iquote1.sub: line 29: recho: command not found
< ./iquote1.sub: line 30: recho: command not found
< ./iquote1.sub: line 31: recho: command not found
< ./iquote1.sub: line 32: recho: command not found
< ./iquote1.sub: line 34: recho: command not found
< ./iquote1.sub: line 35: recho: command not found
< ./iquote1.sub: line 36: recho: command not found
< ./iquote1.sub: line 38: recho: command not found
< ./iquote1.sub: line 39: recho: command not found
< ./iquote1.sub: line 40: recho: command not found
< ./iquote1.sub: line 41: recho: command not found
< ./iquote1.sub: line 43: recho: command not found
< ./iquote1.sub: line 44: recho: command not found
< ./iquote1.sub: line 45: recho: command not found
< ./iquote1.sub: line 46: recho: command not found
< ./iquote1.sub: line 47: recho: command not found
< ./iquote1.sub: line 48: recho: command not found
< ./iquote1.sub: line 49: recho: command not found
< ./iquote1.sub: line 50: recho: command not found
< ./iquote1.sub: line 51: recho: command not found
< ./iquote1.sub: line 52: recho: command not found
< ./iquote1.sub: line 53: recho: command not found
< ./iquote1.sub: line 54: recho: command not found
< ./iquote1.sub: line 55: recho: command not found
< ./iquote1.sub: line 56: recho: command not found
---
> argv[1] = <aaa^?bbb>
> argv[1] = <ccc^?ddd>
> argv[1] = <eee^?fff>
> argv[1] = <ggg^?hhh>
> argv[1] = <aaabbb>
> argv[1] = <cccddd>
> argv[1] = <eeefff>
> argv[1] = <ggghhh>
> argv[1] = <aaa^?bbb>
> argv[1] = <ccc^?ddd>
> argv[1] = <eee^?fff>
> argv[1] = <ggg^?hhh>
> argv[1] = <aaabbb>
> argv[1] = <cccddd>
> argv[1] = <eeefff>
> argv[1] = <ggghhh>
> argv[1] = <aaa^?bbb>
> argv[1] = <ccc^?ddd>
> argv[1] = <eee^?fff>
> argv[1] = <ggg^?hhh>
> argv[1] = <xy>
> argv[1] = <xy>
> argv[1] = <xy>
> argv[1] = <x^?y>
> argv[1] = <>
> argv[1] = <>
> argv[1] = <>
> argv[1] = <>
> argv[1] = <>
> argv[1] = <>
> argv[1] = <^?>
> argv[1] = <^? >
> argv[1] = < ^?>
> argv[1] = < ^?>
> argv[1] = < ^?>
> argv[1] = < ^?>
> argv[1] = < ^?>
> argv[1] = < ^?>
> argv[1] = < ^?>
> argv[1] = < ^?>
> argv[1] = < ^?>
> argv[1] = < ^?x>
> argv[1] = < ^?>
> argv[1] = < ^?>
> argv[1] = < ^?>
> argv[1] = < ^?x>
> argv[1] = <^?x>
> argv[1] = <^?>
> argv[1] = < ^? x>
> argv[1] = <^? x>
> argv[1] = <^? >
run-jobs
19,23c19,23
< [1]   Running                 sleep 2 &
< [2]   Running                 sleep 2 &
< [3]   Running                 sleep 2 &
< [4]-  Running                 sleep 2 &
< [5]+  Running                 ( sleep 2; exit 4 ) &
---
> [1]   Running                    sleep 2 &
> [2]   Running                    sleep 2 &
> [3]   Running                    sleep 2 &
> [4]-  Running                    sleep 2 &
> [5]+  Running                    ( sleep 2; exit 4 ) &
28,29c28,29
< [1]-  Running                 sleep 20 &
< [3]+  Running                 sleep 20 &
---
> [1]-  Running                    sleep 20 &
> [3]+  Running                    sleep 20 &
35c35
< declare -- wpid="-554296800"
---
> ./jobs5.sub: line 71: declare: wpid: not found
42c42
< got 1) SIGHUP 2) SIGINT 3) SIGQUIT 4) SIGILL 5) SIGTRAP 6) SIGABRT 7) SIGBUS 8) SIGFPE 9) SIGKILL 10) SIGUSR1 11) SIGSEGV 12) SIGUSR2 13) SIGPIPE 14) SIGALRM 15) SIGTERM 16) SIGSTKFLT 17) SIGCHLD 18) SIGCONT 19) SIGSTOP 20) SIGTSTP 21) SIGTTIN 22) SIGTTOU 23) SIGURG 24) SIGXCPU 25) SIGXFSZ 26) SIGVTALRM 27) SIGPROF 28) SIGWINCH 29) SIGIO 30) SIGPWR 31) SIGSYS 34) SIGRTMIN 35) SIGRTMIN+1 36) SIGRTMIN+2 37) SIGRTMIN+3 38) SIGRTMIN+4 39) SIGRTMIN+5 40) SIGRTMIN+6 41) SIGRTMIN+7 42) SIGRTMIN+8 43) SIGRTMIN+9 44) SIGRTMIN+10 45) SIGRTMIN+11 46) SIGRTMIN+12 47) SIGRTMIN+13 48) SIGRTMIN+14 49) SIGRTMIN+15 50) SIGRTMAX-14 51) SIGRTMAX-13 52) SIGRTMAX-12 53) SIGRTMAX-11 54) SIGRTMAX-10 55) SIGRTMAX-9 56) SIGRTMAX-8 57) SIGRTMAX-7 58) SIGRTMAX-6 59) SIGRTMAX-5 60) SIGRTMAX-4 61) SIGRTMAX-3 62) SIGRTMAX-2 63) SIGRTMAX-1 64) SIGRTMAX
---
> got USR1
56c56
< [1]+  Done                    sleep 1
---
> [1]+  Done                       sleep 1
81a82
> ./jobs.tests: line 147: disown: warning: @12: job specification requires leading `%'
87,89c88,90
< [1]   Running                 sleep 300 &
< [2]-  Running                 sleep 350 &
< [3]+  Running                 sleep 400 &
---
> [1]   Running                    sleep 300 &
> [2]-  Running                    sleep 350 &
> [3]+  Running                    sleep 400 &
91,93c92,94
< [1]   Running                 sleep 300 &
< [2]-  Running                 sleep 350 &
< [3]+  Running                 sleep 400 &
---
> [1]   Running                    sleep 300 &
> [2]-  Running                    sleep 350 &
> [3]+  Running                    sleep 400 &
97c98
< [3]+  Running                 sleep 400 &
---
> [3]+  Running                    sleep 400 &
99c100
< [2]-  Running                 sleep 350 &
---
> [2]-  Running                    sleep 350 &
102,103c103,104
< [1]   Running                 sleep 300 &
< [3]-  Running                 sleep 400 &
---
> [1]   Running                    sleep 300 &
> [3]-  Running                    sleep 400 &
105c106
< [2]+  Stopped                 sleep 350
---
> [2]+  Stopped                    sleep 350
107,108c108,109
< [2]+  Stopped                 sleep 350
< [3]-  Running                 sleep 400 &
---
> [2]+  Stopped                    sleep 350
> [3]-  Running                    sleep 400 &
110c111
< [3]-  Running                 sleep 400 &
---
> [3]-  Running                    sleep 400 &
112c113
< [2]+  Stopped                 sleep 350
---
> [2]+  Stopped                    sleep 350
115,116c116,117
< [2]+  Running                 sleep 350 &
< [3]-  Running                 sleep 400 &
---
> [2]+  Running                    sleep 350 &
> [3]-  Running                    sleep 400 &
run-lastpipe
22,23c22,23
< x=
< x=
---
> x=x
> x=x
run-mapfile
154c154
< declare -a array=([0]=$'a\377' [1]=$'b\377' [2]=$'c\377' [3]=$'\n')
---
> declare -a array=([0]="a" [1]="b" [2]="c" [3]=$'\n')
run-more-exp
1,87c1,110
< ./more-exp.tests: line 31: recho: command not found
< ./more-exp.tests: line 33: recho: command not found
< ./more-exp.tests: line 42: recho: command not found
< ./more-exp.tests: line 44: recho: command not found
< ./more-exp.tests: line 49: recho: command not found
< ./more-exp.tests: line 51: recho: command not found
< ./more-exp.tests: line 53: recho: command not found
< ./more-exp.tests: line 55: recho: command not found
< ./more-exp.tests: line 59: recho: command not found
< ./more-exp.tests: line 61: recho: command not found
< ./more-exp.tests: line 63: recho: command not found
< ./more-exp.tests: line 67: recho: command not found
< ./more-exp.tests: line 69: recho: command not found
< ./more-exp.tests: line 71: recho: command not found
< ./more-exp.tests: line 73: recho: command not found
< ./more-exp.tests: line 75: recho: command not found
< ./more-exp.tests: line 80: recho: command not found
< ./more-exp.tests: line 85: recho: command not found
< ./more-exp.tests: line 87: recho: command not found
< ./more-exp.tests: line 89: recho: command not found
< ./more-exp.tests: line 91: recho: command not found
< ./more-exp.tests: line 93: recho: command not found
< ./more-exp.tests: line 96: recho: command not found
< ./more-exp.tests: line 98: recho: command not found
< ./more-exp.tests: line 100: recho: command not found
< ./more-exp.tests: line 102: recho: command not found
< ./more-exp.tests: line 104: recho: command not found
< ./more-exp.tests: line 106: recho: command not found
< ./more-exp.tests: line 110: recho: command not found
< ./more-exp.tests: line 112: recho: command not found
< ./more-exp.tests: line 116: recho: command not found
< ./more-exp.tests: line 118: recho: command not found
< ./more-exp.tests: line 121: recho: command not found
< ./more-exp.tests: line 123: recho: command not found
< ./more-exp.tests: line 126: recho: command not found
< ./more-exp.tests: line 128: recho: command not found
< ./more-exp.tests: line 131: recho: command not found
< ./more-exp.tests: line 133: recho: command not found
< ./more-exp.tests: line 140: recho: command not found
< ./more-exp.tests: line 144: recho: command not found
< ./more-exp.tests: line 158: recho: command not found
< ./more-exp.tests: line 167: recho: command not found
< ./more-exp.tests: line 168: recho: command not found
< ./more-exp.tests: line 167: recho: command not found
< ./more-exp.tests: line 168: recho: command not found
< ./more-exp.tests: line 167: recho: command not found
< ./more-exp.tests: line 168: recho: command not found
< ./more-exp.tests: line 167: recho: command not found
< ./more-exp.tests: line 168: recho: command not found
< ./more-exp.tests: line 189: recho: command not found
< ./more-exp.tests: line 191: recho: command not found
< ./more-exp.tests: line 194: recho: command not found
< ./more-exp.tests: line 196: recho: command not found
< ./more-exp.tests: line 199: recho: command not found
< ./more-exp.tests: line 203: recho: command not found
< ./more-exp.tests: line 205: recho: command not found
< ./more-exp.tests: line 207: recho: command not found
< ./more-exp.tests: line 209: recho: command not found
< ./more-exp.tests: line 211: recho: command not found
< ./more-exp.tests: line 213: recho: command not found
< ./more-exp.tests: line 215: recho: command not found
< ./more-exp.tests: line 217: recho: command not found
< ./more-exp.tests: line 222: recho: command not found
< ./more-exp.tests: line 224: recho: command not found
< ./more-exp.tests: line 226: recho: command not found
< ./more-exp.tests: line 228: recho: command not found
< ./more-exp.tests: line 230: recho: command not found
< ./more-exp.tests: line 232: recho: command not found
< ./more-exp.tests: line 234: recho: command not found
< ./more-exp.tests: line 236: recho: command not found
< ./more-exp.tests: line 238: recho: command not found
< ./more-exp.tests: line 241: recho: command not found
< ./more-exp.tests: line 243: recho: command not found
< ./more-exp.tests: line 245: recho: command not found
< ./more-exp.tests: line 247: recho: command not found
< ./more-exp.tests: line 249: recho: command not found
< ./more-exp.tests: line 251: recho: command not found
< ./more-exp.tests: line 253: recho: command not found
< ./more-exp.tests: line 255: recho: command not found
< ./more-exp.tests: line 257: recho: command not found
< ./more-exp.tests: line 259: recho: command not found
< ./more-exp.tests: line 262: recho: command not found
< ./more-exp.tests: line 263: recho: command not found
< ./more-exp.tests: line 266: recho: command not found
< ./more-exp.tests: line 267: recho: command not found
< ./more-exp.tests: line 281: recho: command not found
< ./more-exp.tests: line 282: recho: command not found
---
> argv[1] = <aaa bbb ccc>
> argv[1] = <aaa bbb ccc>
> argv[1] = <baz:bar>
> argv[1] = <baz:bar>
> argv[1] = <aaa bbb ccc>
> argv[1] = <bar>
> argv[1] = <bar>
> argv[1] = <bar>
> argv[1] = <abcde>
> argv[1] = <abcde>
> argv[1] = <xyz>
> argv[1] = <a b>
> argv[2] = <c>
> argv[3] = <d>
> argv[4] = <e>
> argv[5] = <f>
> argv[1] = <a b>
> argv[1] = <a>
> argv[2] = <b>
> argv[1] = <a b>
> argv[2] = <c>
> argv[3] = <d>
> argv[4] = <e>
> argv[5] = <f>
> argv[1] = <a b>
> argv[2] = <c>
> argv[3] = <d>
> argv[4] = <e>
> argv[5] = <f>
> argv[1] = </usr/homes/chet>
> argv[1] = <~>
> argv[1] = <~>
> argv[1] = <\~>
> argv[1] = <\ \~>
> argv[1] = <\ \ \~>
> argv[1] = </usr/homes/chet>
> argv[1] = </usr/homes/chet>
> argv[1] = </usr/homes/chet>
> argv[1] = <$HOME>
> argv[1] = <\ $HOME>
> argv[1] = <\ \ $HOME>
> argv[1] = <'bar'>
> argv[1] = <'bar'>
> argv[1] = <*@>
> argv[1] = <*@>
> argv[1] = <*@>
> argv[1] = <*@>
> argv[1] = <*@*>
> argv[1] = <*@*>
> argv[1] = <*@*>
> argv[1] = <*@*>
> argv[1] = <abcd>
> argv[1] = <efghijkl>
> argv[1] = <4>
> argv[2] = <2>
> argv[1] = <1>
> argv[1] = <bar>
> argv[1] = <2>
> argv[1] = <bar>
> argv[1] = <2>
> argv[1] = <4>
> argv[1] = <--\>
> argv[2] = <-->
> argv[1] = <--\^J-->
> argv[1] = <--+\>
> argv[2] = <+-->
> argv[1] = <--+\^J+-->
> argv[1] = <-+\>
> argv[2] = <+-\>
> argv[3] = <->
> argv[1] = <xy>
> argv[1] = <xy>
> argv[1] = <xy>
> argv[1] = <xy>
> argv[1] = <xy>
> argv[1] = <xy>
> argv[1] = <>
> argv[1] = <>
> argv[1] = <xy>
> argv[1] = <xy>
> argv[1] = <xy>
> argv[1] = <xy>
> argv[1] = <xy>
> argv[1] = <xy>
> argv[1] = <>
> argv[1] = <>
> argv[1] = <x>
> argv[1] = <x>
> argv[1] = <>
> argv[1] = <x>
> argv[1] = <x>
> argv[1] = <x>
> argv[1] = <x>
> argv[1] = <^?>
> argv[1] = <^?>
> argv[1] = <x>
> argv[1] = <x>
> argv[1] = <>
> argv[2] = <abd>
> argv[3] = <x>
> argv[1] = <>
> argv[2] = <abd>
> argv[3] = <>
> argv[1] = <a,b,c,d,e,f>
> argv[1] = <a>
> argv[2] = <b>
> argv[3] = <c>
> argv[4] = <d>
> argv[5] = <e>
> argv[6] = <f>
89,148c112,157
< ./more-exp.tests: line 290: recho: command not found
< ./more-exp.tests: line 291: recho: command not found
< ./more-exp.tests: line 293: recho: command not found
< ./more-exp.tests: line 297: recho: command not found
< ./more-exp.tests: line 298: recho: command not found
< ./more-exp.tests: line 300: recho: command not found
< ./more-exp.tests: line 301: recho: command not found
< ./more-exp.tests: line 303: recho: command not found
< ./more-exp.tests: line 304: recho: command not found
< ./more-exp.tests: line 306: zecho: command not found
< ./more-exp.tests: line 306: recho: command not found
< ./more-exp.tests: line 307: zecho: command not found
< ./more-exp.tests: line 307: recho: command not found
< ./more-exp.tests: line 309: zecho: command not found
< ./more-exp.tests: line 309: recho: command not found
< ./more-exp.tests: line 310: zecho: command not found
< ./more-exp.tests: line 310: recho: command not found
< ./more-exp.tests: line 312: zecho: command not found
< ./more-exp.tests: line 312: recho: command not found
< ./more-exp.tests: line 313: zecho: command not found
< ./more-exp.tests: line 313: recho: command not found
< ./more-exp.tests: line 315: zecho: command not found
< ./more-exp.tests: line 315: recho: command not found
< ./more-exp.tests: line 316: zecho: command not found
< ./more-exp.tests: line 316: recho: command not found
< ./more-exp.tests: line 318: zecho: command not found
< ./more-exp.tests: line 318: recho: command not found
< ./more-exp.tests: line 319: zecho: command not found
< ./more-exp.tests: line 319: recho: command not found
< ./more-exp.tests: line 321: zecho: command not found
< ./more-exp.tests: line 321: recho: command not found
< ./more-exp.tests: line 322: zecho: command not found
< ./more-exp.tests: line 322: recho: command not found
< ./more-exp.tests: line 326: recho: command not found
< ./more-exp.tests: line 327: recho: command not found
< ./more-exp.tests: line 329: recho: command not found
< ./more-exp.tests: line 330: recho: command not found
< ./more-exp.tests: line 332: recho: command not found
< ./more-exp.tests: line 333: recho: command not found
< ./more-exp.tests: line 335: zecho: command not found
< ./more-exp.tests: line 335: zecho: command not found
< ./more-exp.tests: line 335: recho: command not found
< ./more-exp.tests: line 336: zecho: command not found
< ./more-exp.tests: line 336: zecho: command not found
< ./more-exp.tests: line 336: recho: command not found
< ./more-exp.tests: line 338: zecho: command not found
< ./more-exp.tests: line 338: zecho: command not found
< ./more-exp.tests: line 338: recho: command not found
< ./more-exp.tests: line 339: zecho: command not found
< ./more-exp.tests: line 339: zecho: command not found
< ./more-exp.tests: line 339: recho: command not found
< ./more-exp.tests: line 341: zecho: command not found
< ./more-exp.tests: line 341: zecho: command not found
< ./more-exp.tests: line 341: recho: command not found
< ./more-exp.tests: line 342: zecho: command not found
< ./more-exp.tests: line 342: zecho: command not found
< ./more-exp.tests: line 342: recho: command not found
< ./more-exp.tests: line 345: recho: command not found
< ./more-exp.tests: line 350: recho: command not found
< ./more-exp.tests: line 354: recho: command not found
---
> argv[1] = <a b c d e>
> argv[1] = <a>
> argv[2] = <b>
> argv[3] = <c>
> argv[4] = <d>
> argv[5] = <e>
> argv[1] = <foo)>
> argv[1] = <a>
> argv[1] = <\a>
> argv[1] = <\a>
> argv[1] = <\a>
> argv[1] = <\a>
> argv[1] = <\\a>
> argv[1] = <a>
> argv[1] = <\a>
> argv[1] = <\a>
> argv[1] = <\a>
> argv[1] = <\a>
> argv[1] = <\\a>
> argv[1] = <a>
> argv[1] = <a>
> argv[1] = <\a>
> argv[1] = <\a>
> argv[1] = <\a>
> argv[1] = <\a>
> argv[1] = <$a>
> argv[1] = <\foo>
> argv[1] = <$a>
> argv[1] = <\foo>
> argv[1] = <\$a>
> argv[1] = <\\$a>
> argv[1] = <a>
> argv[1] = <a>
> argv[1] = <\a>
> argv[1] = <\a>
> argv[1] = <\a>
> argv[1] = <\a>
> argv[1] = <G>
> argv[2] = <{>
> argv[3] = <I>
> argv[4] = <K>
> argv[5] = <}>
> argv[1] = <hi>
> argv[2] = <K>
> argv[3] = <}>
> argv[1] = <a*>
158,181c167,186
< ./more-exp.tests: line 370: recho: command not found
< ./more-exp.tests: line 372: recho: command not found
< ./more-exp.tests: line 374: recho: command not found
< ./more-exp.tests: line 376: recho: command not found
< ./more-exp.tests: line 378: recho: command not found
< ./more-exp.tests: line 381: recho: command not found
< ./more-exp.tests: line 384: recho: command not found
< ./more-exp.tests: line 386: recho: command not found
< ./more-exp.tests: line 389: recho: command not found
< ./more-exp.tests: line 391: recho: command not found
< ./more-exp.tests: line 396: recho: command not found
< ./more-exp.tests: line 398: recho: command not found
< ./more-exp.tests: line 400: recho: command not found
< ./more-exp.tests: line 402: recho: command not found
< ./more-exp.tests: line 404: recho: command not found
< ./more-exp.tests: line 407: recho: command not found
< ./more-exp.tests: line 409: recho: command not found
< ./more-exp.tests: line 412: recho: command not found
< ./more-exp.tests: line 415: recho: command not found
< ./more-exp.tests: line 418: recho: command not found
< ./more-exp.tests: line 421: recho: command not found
< ./more-exp.tests: line 426: recho: command not found
< ./more-exp.tests: line 428: recho: command not found
< ./more-exp.tests: line 433: recho: command not found
---
> argv[1] = <5>
> argv[1] = <5>
> argv[1] = <5>
> argv[1] = <5>
> argv[1] = <5>
> argv[1] = <0>
> argv[1] = <0>
> argv[1] = <0>
> argv[1] = <0>
> argv[1] = <0>
> argv[1] = <0>
> argv[1] = <posparams>
> argv[1] = <posparams>
> argv[1] = <2>
> argv[1] = <0>
> argv[1] = <0>
> argv[1] = <1>
> argv[1] = <5>
> argv[1] = <5>
> argv[1] = <0>
188,196c193,206
< ./more-exp.tests: line 449: #: %: syntax error: operand expected (error token is "%")
< ./more-exp.tests: line 452: recho: command not found
< ./more-exp.tests: line 463: recho: command not found
< ./more-exp.tests: line 465: recho: command not found
< ./more-exp.tests: line 468: recho: command not found
< ./more-exp.tests: line 470: recho: command not found
< ./more-exp.tests: line 477: recho: command not found
< ./more-exp.tests: line 482: recho: command not found
< ./more-exp.tests: line 493: recho: command not found
---
> ./more-exp.tests: line 449: #: %: arithmetic syntax error: operand expected (error token is "%")
> argv[1] = <0>
> argv[1] = <a+b>
> argv[1] = <+>
> argv[1] = <+>
> argv[1] = <+>
> argv[1] = <G { I >
> argv[2] = <K>
> argv[3] = <}>
> argv[1] = <hi>
> argv[2] = <K>
> argv[3] = <}>
> argv[1] = <xxx>
> argv[2] = <yyy>
198,204c208,214
< ./more-exp.tests: line 500: recho: command not found
< ./more-exp.tests: line 502: recho: command not found
< ./more-exp.tests: line 504: recho: command not found
< ./more-exp.tests: line 509: recho: command not found
< ./more-exp.tests: line 509: recho: command not found
< ./more-exp.tests: line 515: recho: command not found
< ./more-exp.tests: line 517: recho: command not found
---
> argv[1] = <>
> argv[1] = <>
> argv[1] = <>
> argv[1] = <:a:>
> argv[1] = <:b:>
> argv[1] = <>
> argv[1] = <>
run-nameref
13c13
< ./nameref.tests: line 54: recho: command not found
---
> argv[1] = <one>
15c15
< ./nameref.tests: line 59: recho: command not found
---
> argv[1] = <two>
21c21
< ./nameref.tests: line 93: recho: command not found
---
> argv[1] = <one>
23c23
< ./nameref.tests: line 87: recho: command not found
---
> argv[1] = <two>
25c25
< ./nameref.tests: line 96: recho: command not found
---
> argv[1] = <two>
27c27
< ./nameref.tests: line 87: recho: command not found
---
> argv[1] = <three four five>
29c29
< ./nameref.tests: line 100: recho: command not found
---
> argv[1] = <three four five>
45c45
< ./nameref3.sub: line 22: recho: command not found
---
> argv[1] = <unset>
47c47
< ./nameref3.sub: line 24: recho: command not found
---
> argv[1] = <unset>
49c49
< ./nameref3.sub: line 26: recho: command not found
---
> argv[1] = <bar>
73c73
< ./nameref4.sub: line 159: recho: command not found
---
> argv[1] = <a b c d e>
75c75,79
< ./nameref4.sub: line 169: recho: command not found
---
> argv[1] = <zero>
> argv[2] = <one>
> argv[3] = <seven>
> argv[4] = <three>
> argv[5] = <four>
126c130
< ./nameref8.sub: line 18: warning: v: circular name reference
---
> ./nameref8.sub: line 18: warning: v: maximum nameref depth (8) exceeded
132c136
< ./nameref8.sub: line 44: warning: x: circular name reference
---
> ./nameref8.sub: line 44: warning: x: maximum nameref depth (8) exceeded
136c140
< ./nameref8.sub: line 51: warning: v: circular name reference
---
> ./nameref8.sub: line 51: warning: v: maximum nameref depth (8) exceeded
305c309
< ./nameref15.sub: line 14: warning: a: circular name reference
---
> ./nameref15.sub: line 14: warning: a: maximum nameref depth (8) exceeded
314c318
< ./nameref15.sub: line 33: warning: ref: circular name reference
---
> ./nameref15.sub: line 33: warning: ref: maximum nameref depth (8) exceeded
321c325
< ./nameref15.sub: line 46: warning: xxx: circular name reference
---
> ./nameref15.sub: line 46: warning: xxx: maximum nameref depth (8) exceeded
431,435c435,451
< ./nameref18.sub: line 77: recho: command not found
< ./nameref18.sub: line 78: recho: command not found
< ./nameref18.sub: line 80: recho: command not found
< ./nameref18.sub: line 81: recho: command not found
< ./nameref18.sub: line 83: recho: command not found
---
> argv[1] = <1>
> argv[2] = <2>
> argv[3] = <3>
> argv[1] = <1>
> argv[2] = <2>
> argv[3] = <3>
> argv[1] = <1>
> argv[2] = <2>
> argv[3] = <3>
> argv[1] = <1>
> argv[2] = <2>
> argv[3] = <3>
> argv[1] = <1>
> argv[2] = <2>
> argv[3] = <31>
> argv[4] = <2>
> argv[5] = <3>
498,499c514
< ./nameref22.sub: line 21: declare: `bar+': not a valid identifier
< 
---
> many spaces
519d533
< ./nameref23.sub: line 18: a[0]1: syntax error in expression (error token is "1")
520a535
> declare -ai a=([0]="6")
535c550
< declare -ai a=([0]="10")
---
> declare -ai a=([0]="6")
542,543c557,558
< fooa[1] bar
< declare -a a=([0]="" [1]="fooa[1] bar")
---
> foo bar
> declare -a a=([0]="" [1]="foo bar")
549,551c564,565
< ./nameref23.sub: line 92: a[1]4: syntax error in expression (error token is "4")
< 12
< declare -ai a=([0]="0" [1]="12")
---
> 16
> declare -ai a=([0]="0" [1]="16")
555c569
< 0
---
> 3
561c575
< 0
---
> 3
566a581,582
> bash: line 1: r: unbound variable
> ok 3
run-new-exp
1,6c1,6
< ./new-exp.tests: line 29: recho: command not found
< ./new-exp.tests: line 31: recho: command not found
< ./new-exp.tests: line 34: recho: command not found
< ./new-exp.tests: line 36: recho: command not found
< ./new-exp.tests: line 38: recho: command not found
< ./new-exp.tests: line 41: HOME: }: syntax error: operand expected (error token is "}")
---
> argv[1] = <foo bar>
> argv[1] = <foo>
> argv[1] = </usr/homes/chet>
> argv[1] = </usr/homes/chet>
> argv[1] = </usr/homes/chet>
> ./new-exp.tests: line 41: HOME: }: arithmetic syntax error: operand expected (error token is "}")
8,22c8,24
< ./new-exp.tests: line 49: recho: command not found
< ./new-exp.tests: line 51: recho: command not found
< ./new-exp.tests: line 53: recho: command not found
< ./new-exp.tests: line 55: recho: command not found
< ./new-exp.tests: line 57: recho: command not found
< ./new-exp.tests: line 59: recho: command not found
< ./new-exp.tests: line 61: recho: command not found
< ./new-exp.tests: line 65: recho: command not found
< ./new-exp.tests: line 67: recho: command not found
< ./new-exp.tests: line 69: recho: command not found
< ./new-exp.tests: line 72: recho: command not found
< ./new-exp.tests: line 74: recho: command not found
< ./new-exp.tests: line 78: recho: command not found
< ./new-exp.tests: line 80: recho: command not found
< ./new-exp.tests: line 82: recho: command not found
---
> argv[1] = </usr/homes/chet>
> argv[1] = </usr/homes/chet>
> argv[1] = </usr/homes/chet>
> argv[1] = </usr/homes/chet>
> argv[1] = </usr/homes/chet>
> argv[1] = </usr/homes/chet>
> argv[1] = </usr/homes/chet>
> argv[1] = <*@>
> argv[1] = <*@>
> argv[1] = <@*>
> argv[1] = <)>
> argv[1] = <")">
> argv[1] = <-abcd>
> argv[2] = <->
> argv[1] = <-abcd>
> argv[2] = <->
> argv[1] = <-abcd->
29,51c31,61
< ./new-exp.tests: line 108: recho: command not found
< ./new-exp.tests: line 111: recho: command not found
< ./new-exp.tests: line 114: recho: command not found
< ./new-exp.tests: line 117: recho: command not found
< ./new-exp.tests: line 120: recho: command not found
< ./new-exp.tests: line 123: recho: command not found
< ./new-exp.tests: line 127: recho: command not found
< ./new-exp.tests: line 130: recho: command not found
< ./new-exp.tests: line 133: recho: command not found
< ./new-exp.tests: line 136: recho: command not found
< ./new-exp.tests: line 145: recho: command not found
< ./new-exp.tests: line 148: recho: command not found
< ./new-exp.tests: line 151: recho: command not found
< ./new-exp.tests: line 154: recho: command not found
< ./new-exp.tests: line 157: recho: command not found
< ./new-exp.tests: line 160: recho: command not found
< ./new-exp.tests: line 166: recho: command not found
< ./new-exp.tests: line 170: recho: command not found
< ./new-exp.tests: line 173: recho: command not found
< ./new-exp.tests: line 178: recho: command not found
< ./new-exp.tests: line 180: recho: command not found
< ./new-exp.tests: line 183: recho: command not found
< ./new-exp.tests: line 185: recho: command not found
---
> argv[1] = <abcd>
> argv[1] = <efg>
> argv[2] = <nop>
> argv[1] = <efg>
> argv[2] = <nop>
> argv[1] = <hijklmnop>
> argv[1] = <abcdefghijklmnop>
> argv[1] = <abcdefghijklmnop>
> argv[1] = <ab cd>
> argv[2] = <ef>
> argv[1] = <gh ij>
> argv[2] = <kl mn>
> argv[1] = <gh ij>
> argv[2] = <kl mn>
> argv[3] = <op>
> argv[1] = <ab cd>
> argv[2] = <ef>
> argv[3] = <gh ij>
> argv[4] = <kl mn>
> argv[5] = <op>
> argv[1] = </home/chet/foo//bar/abcabcabc>
> argv[1] = <home/chet/foo//bar/abcabcabc>
> argv[1] = <home>
> argv[1] = <home>
> argv[1] = <home>
> argv[1] = <home>
> argv[1] = <abcdefghijklmnop>
> argv[1] = <4>
> argv[1] = <op>
> argv[1] = <abcdefghijklmnop>
> argv[1] = <abcdefghijklmnop>
53,54c63,69
< ./new-exp.tests: line 196: recho: command not found
< ./new-exp.tests: line 198: recho: command not found
---
> argv[1] = <a>
> argv[2] = <b>
> argv[3] = <c>
> argv[4] = <d>
> argv[1] = <a>
> argv[2] = <b c>
> argv[3] = <d>
57,88c72,163
< ./new-exp.tests: line 212: recho: command not found
< ./new-exp.tests: line 214: recho: command not found
< ./new-exp.tests: line 216: recho: command not found
< ./new-exp.tests: line 218: recho: command not found
< ./new-exp.tests: line 220: recho: command not found
< ./new-exp.tests: line 222: recho: command not found
< ./new-exp.tests: line 224: recho: command not found
< ./new-exp.tests: line 226: recho: command not found
< ./new-exp.tests: line 231: recho: command not found
< ./new-exp.tests: line 233: recho: command not found
< ./new-exp.tests: line 235: recho: command not found
< ./new-exp.tests: line 237: recho: command not found
< ./new-exp.tests: line 239: recho: command not found
< ./new-exp.tests: line 241: recho: command not found
< ./new-exp.tests: line 243: recho: command not found
< ./new-exp.tests: line 245: recho: command not found
< ./new-exp.tests: line 247: recho: command not found
< ./new-exp.tests: line 250: recho: command not found
< ./new-exp.tests: line 252: recho: command not found
< ./new-exp.tests: line 254: recho: command not found
< ./new-exp.tests: line 256: recho: command not found
< ./new-exp.tests: line 258: recho: command not found
< ./new-exp.tests: line 263: recho: command not found
< ./new-exp.tests: line 265: recho: command not found
< ./new-exp.tests: line 267: recho: command not found
< ./new-exp.tests: line 269: recho: command not found
< ./new-exp.tests: line 271: recho: command not found
< ./new-exp.tests: line 273: recho: command not found
< ./new-exp.tests: line 275: recho: command not found
< ./new-exp.tests: line 277: recho: command not found
< ./new-exp.tests: line 279: recho: command not found
< ./new-exp.tests: line 281: recho: command not found
---
> argv[1] = <xxcde>
> argv[1] = <axxde>
> argv[1] = <abxyz>
> argv[1] = <abbcde>
> argv[1] = <abcde>
> argv[1] = <abcabe>
> argv[1] = <abcdlast>
> argv[1] = <abcde>
> argv[1] = <xxcd>
> argv[1] = <abxx>
> argv[1] = <xxgh>
> argv[1] = <efgh>
> argv[1] = <xxfgh>
> argv[1] = <zagh>
> argv[1] = <zaza>
> argv[1] = <zagh>
> argv[1] = <efza>
> argv[1] = <yyy>
> argv[2] = <yyy>
> argv[3] = <yyy>
> argv[4] = <yyy>
> argv[5] = <yyy>
> argv[6] = <yyy>
> argv[1] = <yyy>
> argv[2] = <yyy>
> argv[3] = <yyy>
> argv[4] = <yyy>
> argv[5] = <yyy>
> argv[6] = <yyy>
> argv[1] = <yyy>
> argv[2] = <yyy>
> argv[3] = <yyy>
> argv[4] = <yyy>
> argv[5] = <yyy>
> argv[6] = <yyy>
> argv[1] = <yyy>
> argv[2] = <efgh>
> argv[3] = <ijkl>
> argv[4] = <mnop>
> argv[5] = <qrst>
> argv[6] = <uvwx>
> argv[1] = <abxx>
> argv[2] = <efxx>
> argv[3] = <ijxx>
> argv[4] = <mnxx>
> argv[5] = <qrxx>
> argv[6] = <uvxx>
> argv[1] = <xxcd>
> argv[1] = <xxcd>
> argv[2] = <xxgh>
> argv[3] = <xxkl>
> argv[4] = <xxop>
> argv[5] = <xxst>
> argv[6] = <xxwx>
> argv[1] = <abxx>
> argv[2] = <efxx>
> argv[3] = <ijxx>
> argv[4] = <mnxx>
> argv[5] = <qrxx>
> argv[6] = <uvxx>
> argv[1] = <zaza>
> argv[1] = <ijza>
> argv[1] = <zaza>
> argv[2] = <zaza>
> argv[3] = <zaza>
> argv[4] = <zaza>
> argv[5] = <zaza>
> argv[6] = <zaza>
> argv[1] = <zacd>
> argv[2] = <zagh>
> argv[3] = <zakl>
> argv[4] = <zaop>
> argv[5] = <zast>
> argv[6] = <zawx>
> argv[1] = <yyy>
> argv[2] = <yyy>
> argv[3] = <yyy>
> argv[4] = <yyy>
> argv[5] = <yyy>
> argv[6] = <yyy>
> argv[1] = <yyy>
> argv[2] = <efgh>
> argv[3] = <ijkl>
> argv[4] = <mnop>
> argv[5] = <qrst>
> argv[6] = <uvwx>
> argv[1] = <abcd>
> argv[2] = <efgh>
> argv[3] = <ijkl>
> argv[4] = <mnop>
> argv[5] = <qrst>
> argv[6] = <uvwyyy>
104c179
< ./new-exp.tests: line 305: recho: command not found
---
> argv[1] = <6>
106,173c181,257
< ./new-exp.tests: line 310: recho: command not found
< ./new-exp.tests: line 312: recho: command not found
< ./new-exp.tests: line 314: recho: command not found
< ./new-exp.tests: line 322: recho: command not found
< ./new-exp.tests: line 324: recho: command not found
< ./new-exp.tests: line 326: recho: command not found
< ./new-exp.tests: line 330: recho: command not found
< ./new-exp.tests: line 332: recho: command not found
< ./new-exp.tests: line 336: recho: command not found
< ./new-exp.tests: line 338: recho: command not found
< ./new-exp.tests: line 341: recho: command not found
< ./new-exp.tests: line 343: recho: command not found
< ./new-exp.tests: line 346: recho: command not found
< ./new-exp.tests: line 348: recho: command not found
< ./new-exp.tests: line 351: recho: command not found
< ./new-exp.tests: line 355: recho: command not found
< ./new-exp.tests: line 359: recho: command not found
< ./new-exp.tests: line 361: recho: command not found
< ./new-exp.tests: line 363: recho: command not found
< ./new-exp.tests: line 367: recho: command not found
< ./new-exp.tests: line 369: recho: command not found
< ./new-exp.tests: line 371: recho: command not found
< ./new-exp.tests: line 373: recho: command not found
< ./new-exp.tests: line 376: recho: command not found
< ./new-exp.tests: line 378: recho: command not found
< ./new-exp.tests: line 380: recho: command not found
< ./new-exp.tests: line 383: recho: command not found
< ./new-exp.tests: line 385: recho: command not found
< ./new-exp.tests: line 387: recho: command not found
< ./new-exp.tests: line 389: recho: command not found
< ./new-exp.tests: line 393: recho: command not found
< ./new-exp.tests: line 394: recho: command not found
< ./new-exp.tests: line 396: recho: command not found
< ./new-exp.tests: line 398: recho: command not found
< ./new-exp.tests: line 399: recho: command not found
< ./new-exp.tests: line 401: recho: command not found
< ./new-exp.tests: line 402: recho: command not found
< ./new-exp.tests: line 403: recho: command not found
< ./new-exp.tests: line 406: recho: command not found
< ./new-exp.tests: line 409: recho: command not found
< ./new-exp.tests: line 415: recho: command not found
< ./new-exp.tests: line 416: recho: command not found
< ./new-exp.tests: line 417: recho: command not found
< ./new-exp.tests: line 418: recho: command not found
< ./new-exp.tests: line 422: recho: command not found
< ./new-exp.tests: line 423: recho: command not found
< ./new-exp.tests: line 425: recho: command not found
< ./new-exp.tests: line 426: recho: command not found
< ./new-exp.tests: line 429: recho: command not found
< ./new-exp.tests: line 430: recho: command not found
< ./new-exp.tests: line 433: recho: command not found
< ./new-exp.tests: line 434: recho: command not found
< ./new-exp.tests: line 438: recho: command not found
< ./new-exp.tests: line 439: recho: command not found
< ./new-exp.tests: line 440: recho: command not found
< ./new-exp.tests: line 446: recho: command not found
< ./new-exp.tests: line 449: recho: command not found
< ./new-exp.tests: line 453: recho: command not found
< ./new-exp.tests: line 457: recho: command not found
< ./new-exp.tests: line 459: recho: command not found
< ./new-exp.tests: line 466: recho: command not found
< ./new-exp.tests: line 467: recho: command not found
< ./new-exp.tests: line 469: recho: command not found
< ./new-exp.tests: line 470: recho: command not found
< ./new-exp.tests: line 472: recho: command not found
< ./new-exp.tests: line 473: recho: command not found
< ./new-exp.tests: line 474: recho: command not found
< ./new-exp.tests: line 475: recho: command not found
---
> argv[1] = <'>
> argv[1] = <">
> argv[1] = <"hello">
> argv[1] = <>
> argv[1] = <>
> argv[1] = <>
> argv[1] = <abcdef>
> argv[1] = <abc def>
> argv[1] = <abcdef>
> argv[1] = <abc>
> argv[2] = <def>
> argv[1] = <abcdef>
> argv[1] = <abc def>
> argv[1] = <abcdef>
> argv[1] = <abc def>
> argv[1] = <ab>
> argv[2] = <cd>
> argv[3] = <ef>
> argv[4] = <gh>
> argv[1] = <ab>
> argv[2] = <cd>
> argv[3] = <ef>
> argv[4] = <gh>
> argv[1] = <ab>
> argv[2] = <cd>
> argv[3] = <ef>
> argv[4] = <gh>
> argv[1] = <>
> argv[1] = <>
> argv[1] = <>
> argv[1] = <>
> argv[1] = <>
> argv[1] = <>
> argv[1] = <hijklmnopqrstuv>
> argv[1] = <pqrstuv>
> argv[1] = <uvwxyz>
> argv[1] = <abcdefghijklmnopqrstuvwxyz>
> argv[1] = <abcdefghijklmnopqrst>
> argv[1] = <klmnopq>
> argv[1] = <klmnopq>
> argv[1] = <klmnopq>
> argv[1] = <"2 3">
> argv[1] = <"2:3">
> argv[1] = <"34">
> argv[1] = <"3456">
> argv[1] = <"3456">
> argv[1] = <"3456">
> argv[1] = <^A>
> argv[2] = <^B>
> argv[3] = <^?>
> argv[1] = <^A>
> argv[2] = <^B>
> argv[3] = <^?>
> argv[1] = <^A>
> argv[2] = <^B>
> argv[3] = <^?>
> argv[1] = <^A>
> argv[2] = <^B>
> argv[3] = <^?>
> argv[1] = <one/two>
> argv[1] = <one/two>
> argv[1] = <two>
> argv[1] = <oneonetwo>
> argv[1] = <onetwo>
> argv[1] = <two>
> argv[1] = <oneonetwo>
> argv[1] = <a>
> argv[1] = <defghi>
> argv[1] = <efghi>
> argv[1] = <e*docrine>
> argv[1] = <e*docri*e>
> argv[1] = <endocrine>
> argv[1] = <endocrine>
> argv[1] = <endocrine>
> argv[1] = <endocrine>
> argv[1] = <endocrine>
> argv[1] = <endocrine>
180,196c264,414
< ./new-exp.tests: line 493: recho: command not found
< ./new-exp.tests: line 497: recho: command not found
< ./new-exp.tests: line 498: recho: command not found
< ./new-exp.tests: line 500: recho: command not found
< ./new-exp.tests: line 501: recho: command not found
< ./new-exp.tests: line 503: recho: command not found
< ./new-exp.tests: line 504: recho: command not found
< ./new-exp.tests: line 506: recho: command not found
< ./new-exp.tests: line 507: recho: command not found
< ./new-exp.tests: line 511: recho: command not found
< ./new-exp.tests: line 512: recho: command not found
< ./new-exp.tests: line 514: recho: command not found
< ./new-exp.tests: line 515: recho: command not found
< ./new-exp.tests: line 517: recho: command not found
< ./new-exp.tests: line 518: recho: command not found
< ./new-exp.tests: line 520: recho: command not found
< ./new-exp.tests: line 521: recho: command not found
---
> argv[1] = </usr/bin>
> argv[2] = </bin>
> argv[3] = </usr/local/bin>
> argv[4] = </usr/gnu/bin>
> argv[5] = </usr/bin/X11>
> argv[6] = </sbin>
> argv[7] = </usr/sbin>
> argv[1] = <r>
> argv[2] = <s>
> argv[3] = <t>
> argv[4] = <u>
> argv[5] = <v>
> argv[6] = <w>
> argv[7] = <x>
> argv[8] = <y>
> argv[9] = <z>
> argv[1] = <r>
> argv[2] = <s>
> argv[3] = <t>
> argv[4] = <u>
> argv[5] = <v>
> argv[6] = <w>
> argv[7] = <x>
> argv[8] = <y>
> argv[9] = <z>
> argv[1] = <r>
> argv[2] = <s>
> argv[3] = <t>
> argv[4] = <u>
> argv[5] = <v>
> argv[6] = <w>
> argv[7] = <x>
> argv[8] = <y>
> argv[9] = <z>
> argv[1] = <r>
> argv[2] = <s>
> argv[3] = <t>
> argv[4] = <u>
> argv[5] = <v>
> argv[6] = <w>
> argv[7] = <x>
> argv[8] = <y>
> argv[9] = <z>
> argv[1] = <a>
> argv[2] = <a>
> argv[3] = <a>
> argv[4] = <a>
> argv[5] = <a>
> argv[6] = <a>
> argv[7] = <a>
> argv[8] = <a>
> argv[9] = <a>
> argv[1] = <a>
> argv[2] = <a>
> argv[3] = <a>
> argv[4] = <a>
> argv[5] = <a>
> argv[6] = <a>
> argv[7] = <a>
> argv[8] = <a>
> argv[9] = <a>
> argv[1] = <r>
> argv[2] = <s>
> argv[3] = <t>
> argv[4] = <u>
> argv[5] = <v>
> argv[6] = <w>
> argv[7] = <x>
> argv[8] = <y>
> argv[9] = <z>
> argv[1] = <r>
> argv[2] = <s>
> argv[3] = <t>
> argv[4] = <u>
> argv[5] = <v>
> argv[6] = <w>
> argv[7] = <x>
> argv[8] = <y>
> argv[9] = <z>
> argv[1] = <r>
> argv[2] = <s>
> argv[3] = <t>
> argv[4] = <u>
> argv[5] = <v>
> argv[6] = <w>
> argv[7] = <x>
> argv[8] = <y>
> argv[9] = <z>
> argv[1] = <r>
> argv[2] = <s>
> argv[3] = <t>
> argv[4] = <u>
> argv[5] = <v>
> argv[6] = <w>
> argv[7] = <x>
> argv[8] = <y>
> argv[9] = <z>
> argv[1] = <r>
> argv[2] = <s>
> argv[3] = <t>
> argv[4] = <u>
> argv[5] = <v>
> argv[6] = <w>
> argv[7] = <x>
> argv[8] = <y>
> argv[9] = <z>
> argv[1] = <r>
> argv[2] = <s>
> argv[3] = <t>
> argv[4] = <u>
> argv[5] = <v>
> argv[6] = <w>
> argv[7] = <x>
> argv[8] = <y>
> argv[9] = <z>
> argv[1] = <a>
> argv[2] = <a>
> argv[3] = <a>
> argv[4] = <a>
> argv[5] = <a>
> argv[6] = <a>
> argv[7] = <a>
> argv[8] = <a>
> argv[9] = <a>
> argv[1] = <a>
> argv[2] = <a>
> argv[3] = <a>
> argv[4] = <a>
> argv[5] = <a>
> argv[6] = <a>
> argv[7] = <a>
> argv[8] = <a>
> argv[9] = <a>
> argv[1] = <r>
> argv[2] = <s>
> argv[3] = <t>
> argv[4] = <u>
> argv[5] = <v>
> argv[6] = <w>
> argv[7] = <x>
> argv[8] = <y>
> argv[9] = <z>
> argv[1] = <r>
> argv[2] = <s>
> argv[3] = <t>
> argv[4] = <u>
> argv[5] = <v>
> argv[6] = <w>
> argv[7] = <x>
> argv[8] = <y>
> argv[9] = <z>
204,214c422,456
< ./new-exp.tests: line 535: recho: command not found
< ./new-exp.tests: line 537: recho: command not found
< ./new-exp.tests: line 539: recho: command not found
< ./new-exp.tests: line 541: recho: command not found
< ./new-exp3.sub: line 23: recho: command not found
< ./new-exp3.sub: line 24: recho: command not found
< ./new-exp3.sub: line 28: recho: command not found
< ./new-exp3.sub: line 29: recho: command not found
< ./new-exp3.sub: line 31: recho: command not found
< ./new-exp3.sub: line 32: recho: command not found
< ./new-exp3.sub: line 34: recho: command not found
---
> argv[1] = <5>
> argv[1] = <#>
> argv[1] = <#>
> argv[1] = <>
> argv[1] = <_QUANTITY>
> argv[2] = <_QUART>
> argv[3] = <_QUEST>
> argv[4] = <_QUILL>
> argv[5] = <_QUOTA>
> argv[6] = <_QUOTE>
> argv[1] = <_QUANTITY>
> argv[2] = <_QUART>
> argv[3] = <_QUEST>
> argv[4] = <_QUILL>
> argv[5] = <_QUOTA>
> argv[6] = <_QUOTE>
> argv[1] = <_QUANTITY>
> argv[2] = <_QUART>
> argv[3] = <_QUEST>
> argv[4] = <_QUILL>
> argv[5] = <_QUOTA>
> argv[6] = <_QUOTE>
> argv[1] = <_QUANTITY-_QUART-_QUEST-_QUILL-_QUOTA-_QUOTE>
> argv[1] = <_QUANTITY>
> argv[2] = <_QUART>
> argv[3] = <_QUEST>
> argv[4] = <_QUILL>
> argv[5] = <_QUOTA>
> argv[6] = <_QUOTE>
> argv[1] = <_QUANTITY>
> argv[2] = <_QUART>
> argv[3] = <_QUEST>
> argv[4] = <_QUILL>
> argv[5] = <_QUOTA>
> argv[6] = <_QUOTE>
227,233c469,484
< ./new-exp.tests: line 554: recho: command not found
< ./new-exp.tests: line 557: recho: command not found
< ./new-exp.tests: line 560: recho: command not found
< ./new-exp.tests: line 562: recho: command not found
< ./new-exp.tests: line 563: recho: command not found
< ./new-exp.tests: line 564: recho: command not found
< ./new-exp.tests: line 566: recho: command not found
---
> argv[1] = <a>
> argv[2] = <b>
> argv[3] = <c>
> argv[4] = <d>
> argv[5] = <e>
> argv[6] = <f>
> argv[7] = <g>
> argv[1] = <a>
> argv[2] = <b>
> argv[3] = <c>
> argv[4] = <d>
> argv[5] = <e>
> argv[1] = <a>
> argv[1] = <a>
> argv[2] = <b>
> argv[1] = <>
236,243c487,517
< ./new-exp.tests: line 577: recho: command not found
< ./new-exp.tests: line 578: recho: command not found
< ./new-exp.tests: line 580: recho: command not found
< ./new-exp.tests: line 581: recho: command not found
< ./new-exp.tests: line 585: recho: command not found
< ./new-exp.tests: line 586: recho: command not found
< ./new-exp.tests: line 587: recho: command not found
< ./new-exp.tests: line 588: recho: command not found
---
> argv[1] = <bin>
> argv[2] = <bin>
> argv[3] = <ucb>
> argv[4] = <bin>
> argv[5] = <.>
> argv[6] = <sbin>
> argv[7] = <sbin>
> argv[1] = </>
> argv[2] = </>
> argv[3] = </>
> argv[4] = </>
> argv[5] = </>
> argv[6] = </>
> argv[1] = <bin>
> argv[2] = <usr/bin>
> argv[3] = <usr/ucb>
> argv[4] = <usr/local/bin>
> argv[5] = <.>
> argv[6] = <sbin>
> argv[7] = <usr/sbin>
> argv[1] = </bin>
> argv[2] = </usr/bin>
> argv[3] = </usr/ucb>
> argv[4] = </usr/local/bin>
> argv[5] = <.>
> argv[6] = </sbin>
> argv[7] = </usr/sbin>
> argv[1] = </full/path/to>
> argv[1] = </>
> argv[1] = <full/path/to/x16>
> argv[1] = <x16>
271,286c545,560
< ./new-exp6.sub: line 19: recho: command not found
< ./new-exp6.sub: line 20: recho: command not found
< ./new-exp6.sub: line 21: recho: command not found
< ./new-exp6.sub: line 22: recho: command not found
< ./new-exp6.sub: line 24: recho: command not found
< ./new-exp6.sub: line 25: recho: command not found
< ./new-exp6.sub: line 27: recho: command not found
< ./new-exp6.sub: line 28: recho: command not found
< ./new-exp6.sub: line 30: recho: command not found
< ./new-exp6.sub: line 31: recho: command not found
< ./new-exp6.sub: line 33: recho: command not found
< ./new-exp6.sub: line 34: recho: command not found
< ./new-exp6.sub: line 35: recho: command not found
< ./new-exp6.sub: line 40: recho: command not found
< ./new-exp6.sub: line 41: recho: command not found
< ./new-exp6.sub: line 42: recho: command not found
---
> argv[1] = <>
> argv[1] = <+>
> argv[1] = <+^?>
> argv[1] = <+>
> argv[1] = <^?2>
> argv[1] = <^?2>
> argv[1] = <^?>
> argv[1] = <^?>
> argv[1] = <>
> argv[1] = <>
> argv[1] = <>
> argv[1] = <>
> argv[1] = <12>
> argv[1] = <>
> argv[1] = <>
> argv[1] = </tmp/test/TEST>
355d628
< ./new-exp10.sub: line 43: recho: command not found
362c635
< $'\001'
---
> $'\001\001'
381,386c654,659
< ./new-exp10.sub: line 127: recho: command not found
< ./new-exp10.sub: line 130: recho: command not found
< ./new-exp10.sub: line 133: recho: command not found
< ./new-exp10.sub: line 137: recho: command not found
< ./new-exp10.sub: line 143: recho: command not found
< ./new-exp10.sub: line 147: recho: command not found
---
> argv[1] = <host(2)[5.3]$ >
> argv[1] = <~$ >
> argv[1] = <^A[0]~$ >
> argv[1] = <^A^G^B[0:1]~\$ >
> argv[1] = </ bash$ >
> argv[1] = <1^J/ bash$ >
398,399d670
< ./new-exp11.sub: line 39: recho: command not found
< ./new-exp11.sub: line 40: recho: command not found
445c716,717
< ./new-exp14.sub: line 24: ${foo@k}: bad substitution
---
> 'string'
> 'value with spaces'
447d718
< ./new-exp14.sub: line 26: ${bar@k}: bad substitution
452c723,730
< ./new-exp14.sub: line 36: ${foo[@]@k}: bad substitution
---
> argv[1] = <0>
> argv[2] = <zero z>
> argv[3] = <1>
> argv[4] = <one o>
> argv[5] = <2>
> argv[6] = <two t>
> argv[7] = <3>
> argv[8] = <three t>
464d741
< ./new-exp16.sub: line 19: shopt: patsub_replacement: invalid shell option name
472,475c749,751
< ./new-exp16.sub: line 32: shopt: patsub_replacement: invalid shell option name
< $'&' $'&' $'&' $'&' $'&' $'&' $'&'
< & & & & & & &
< & & & & & & & 
---
> $'a' $'b' $'c' $'d' $'e' $'f' $'g'
> a b c d e f g
> a b c d e f g 
482,483c758,759
< & defg
< & defg
---
> abc defg
> abc defg
488,489c764,765
< \& defg
< &defg
---
> \abc defg
> abcdefg
490a767
> \abcdefg
493c770
< \&defg
---
> \abcdefg
495,496d771
< \\&defg
< ./new-exp16.sub: line 66: shopt: patsub_replacement: invalid shell option name
502,504d776
< ./new-exp16.sub: line 74: shopt: patsub_replacement: invalid shell option name
< letx&yee
< letx&yee
506a779,780
> letxssyee
> letxssyee
509,512c783,784
< letx\&yee
< letx\&yee
< let\&ee
< let\\\&ee
---
> letx&yee
> letx&yee
514c786,788
< let\\&ee
---
> let\\ssee
> let\ssee
> let\ssee
518,519c792,793
< let\&ee
< &twoone
---
> let&ee
> twoone
520a795
> onetwo
522,523c797
< one&two
< &two
---
> two
524a799
> otwone
526,528c801,802
< &twone
< ./new-exp.tests: line 646: recho: command not found
< ./new-exp.tests: line 647: recho: command not found
---
> argv[1] = </>
> argv[1] = </>
run-nquote
1,16c1,17
< ./nquote.tests: line 20: recho: command not found
< ./nquote.tests: line 24: recho: command not found
< ./nquote.tests: line 29: recho: command not found
< ./nquote.tests: line 34: recho: command not found
< ./nquote.tests: line 37: recho: command not found
< ./nquote.tests: line 40: recho: command not found
< ./nquote.tests: line 45: recho: command not found
< ./nquote.tests: line 48: recho: command not found
< ./nquote.tests: line 52: recho: command not found
< ./nquote.tests: line 57: recho: command not found
< ./nquote.tests: line 60: recho: command not found
< ./nquote.tests: line 63: recho: command not found
< ./nquote.tests: line 66: recho: command not found
< ./nquote.tests: line 69: recho: command not found
< ./nquote.tests: line 72: recho: command not found
< ./nquote.tests: line 75: recho: command not found
---
> argv[1] = <^J^J^J>
> argv[1] = <++^J++>
> argv[1] = <>
> argv[1] = <^J^I >
> argv[1] = <abc>
> argv[1] = <^M^[^Gabc>
> argv[1] = <hello,>
> argv[2] = <world>
> argv[1] = <hello, world>
> argv[1] = <>
> argv[1] = <$hello, world>
> argv[1] = <hello, $world>
> argv[1] = <hello, "world">
> argv[1] = <hello, $"world">
> argv[1] = <hello, $"world">
> argv[1] = <$hello, chet>
> argv[1] = <hello, chet>
22,24c23,25
< ./nquote.tests: line 97: recho: command not found
< ./nquote.tests: line 99: recho: command not found
< ./nquote.tests: line 102: recho: command not found
---
> argv[1] = <A\CB>
> argv[1] = <A\CB>
> argv[1] = <ab$cde>
28,31c29,32
< ./nquote.tests: line 111: recho: command not found
< ./nquote.tests: line 112: recho: command not found
< ./nquote.tests: line 113: recho: command not found
< ./nquote.tests: line 115: recho: command not found
---
> argv[1] = <hello, $"world">
> argv[1] = <hello, \$"world">
> argv[1] = <hello, $"world">
> argv[1] = <hello, $world>
35,38c36,39
< ./nquote.tests: line 128: recho: command not found
< ./nquote.tests: line 129: recho: command not found
< ./nquote.tests: line 132: recho: command not found
< ./nquote.tests: line 133: recho: command not found
---
> argv[1] = <^I>
> argv[1] = <'A^IB'>
> argv[1] = <a^Ib^Ic>
> argv[1] = <$'a\tb\tc'>
62c63
< ./nquote3.sub: line 3: recho: command not found
---
> argv[1] = <^?>
70,73c71,74
< ./nquote5.sub: line 16: recho: command not found
< ./nquote5.sub: line 17: recho: command not found
< ./nquote5.sub: line 18: recho: command not found
< ./nquote5.sub: line 19: recho: command not found
---
> argv[1] = <a^A)b>
> argv[1] = <a^Ab>
> argv[1] = <^A>
> argv[1] = <\^A>
78,79c79,80
< 0000000 A a 001 b \n A \n
< 0000007
---
> 0000000 A \n A \n
> 0000004
run-nquote1
1,35c1,92
< ./nquote1.tests: line 24: recho: command not found
< ./nquote1.tests: line 25: recho: command not found
< ./nquote1.tests: line 26: recho: command not found
< ./nquote1.tests: line 27: recho: command not found
< ./nquote1.tests: line 28: recho: command not found
< ./nquote1.tests: line 30: recho: command not found
< ./nquote1.tests: line 31: recho: command not found
< ./nquote1.tests: line 32: recho: command not found
< ./nquote1.tests: line 33: recho: command not found
< ./nquote1.tests: line 34: recho: command not found
< ./nquote1.tests: line 36: recho: command not found
< ./nquote1.tests: line 37: recho: command not found
< ./nquote1.tests: line 38: recho: command not found
< ./nquote1.tests: line 39: recho: command not found
< ./nquote1.tests: line 40: recho: command not found
< ./nquote1.tests: line 42: recho: command not found
< ./nquote1.tests: line 43: recho: command not found
< ./nquote1.tests: line 44: recho: command not found
< ./nquote1.tests: line 45: recho: command not found
< ./nquote1.tests: line 46: recho: command not found
< ./nquote1.tests: line 50: recho: command not found
< ./nquote1.tests: line 51: recho: command not found
< ./nquote1.tests: line 52: recho: command not found
< ./nquote1.tests: line 53: recho: command not found
< ./nquote1.tests: line 58: recho: command not found
< ./nquote1.tests: line 59: recho: command not found
< ./nquote1.tests: line 61: recho: command not found
< ./nquote1.tests: line 62: recho: command not found
< ./nquote1.tests: line 66: recho: command not found
< ./nquote1.tests: line 67: recho: command not found
< ./nquote1.tests: line 69: recho: command not found
< ./nquote1.tests: line 70: recho: command not found
< ./nquote1.tests: line 72: recho: command not found
< ./nquote1.tests: line 74: recho: command not found
< ./nquote1.tests: line 78: recho: command not found
---
> argv[1] = <a>
> argv[2] = <a^Ab>
> argv[3] = <3>
> argv[1] = <1>
> argv[2] = <a^Ab>
> argv[3] = <3>
> argv[1] = <b>
> argv[2] = <a^Ab>
> argv[3] = <3>
> argv[1] = <c>
> argv[2] = <a^Ab>
> argv[3] = <3>
> argv[1] = <d>
> argv[2] = <a^Ab>
> argv[3] = <3>
> argv[1] = <a>
> argv[2] = <a^Ab>
> argv[3] = <3>
> argv[1] = <1>
> argv[2] = <a^Ab>
> argv[3] = <3>
> argv[1] = <b>
> argv[2] = <a^Ab>
> argv[3] = <3>
> argv[1] = <c>
> argv[2] = <a^Ab>
> argv[3] = <3>
> argv[1] = <d>
> argv[2] = <a^Ab>
> argv[3] = <3>
> argv[1] = <a>
> argv[2] = <a^Ab>
> argv[3] = <3>
> argv[1] = <1>
> argv[2] = <a^Ab>
> argv[3] = <3>
> argv[1] = <b>
> argv[2] = <a^Ab>
> argv[3] = <3>
> argv[1] = <c>
> argv[2] = <a^Ab>
> argv[3] = <3>
> argv[1] = <d>
> argv[2] = <a^Ab>
> argv[3] = <3>
> argv[1] = <a>
> argv[2] = <a^Ab>
> argv[3] = <3>
> argv[1] = <1>
> argv[2] = <a^Ab>
> argv[3] = <3>
> argv[1] = <b>
> argv[2] = <a^Ab>
> argv[3] = <3>
> argv[1] = <c>
> argv[2] = <a^Ab>
> argv[3] = <3>
> argv[1] = <d>
> argv[2] = <a^Ab>
> argv[3] = <3>
> argv[1] = <e1>
> argv[2] = <v^A^A>
> argv[1] = <e2>
> argv[2] = <v^A^A>
> argv[1] = <e3>
> argv[2] = <v^A^A>
> argv[1] = <e4>
> argv[2] = <v^A^A>
> argv[1] = <a1>
> argv[2] = <uv^A^A>
> argv[1] = <a2>
> argv[2] = <uv^A^A>
> argv[1] = <a3>
> argv[2] = <uv^A^Awx>
> argv[3] = <uv^A^Awx>
> argv[1] = <a4>
> argv[2] = <uv^A^Awx>
> argv[3] = <uv^A^Awx>
> argv[1] = <p1>
> argv[2] = <uv^A^Awx>
> argv[3] = <uv^A^Awx>
> argv[1] = <p2>
> argv[2] = <uv^A^Awx>
> argv[3] = <uv^A^Awx>
> argv[1] = <p1>
> argv[2] = <uv^A^Awx>
> argv[3] = <uv^A^Awx>
> argv[1] = <p2>
> argv[2] = <uv^A^Awx uv^A^Awx>
> argv[1] = <uv^A^Awx>
> argv[1] = <uv^A^Awx>
> argv[1] = <uv^A^Awx>
39,54c96,131
< ./nquote1.tests: line 92: recho: command not found
< ./nquote1.tests: line 93: recho: command not found
< ./nquote1.tests: line 98: recho: command not found
< ./nquote1.tests: line 99: recho: command not found
< ./nquote1.tests: line 100: recho: command not found
< ./nquote1.tests: line 101: recho: command not found
< ./nquote1.tests: line 103: recho: command not found
< ./nquote1.tests: line 104: recho: command not found
< ./nquote1.tests: line 106: recho: command not found
< ./nquote1.tests: line 107: recho: command not found
< ./nquote1.tests: line 109: recho: command not found
< ./nquote1.tests: line 110: recho: command not found
< ./nquote1.tests: line 115: recho: command not found
< ./nquote1.tests: line 116: recho: command not found
< ./nquote1.tests: line 118: recho: command not found
< ./nquote1.tests: line 119: recho: command not found
---
> argv[1] = <f1>
> argv[2] = <v^Aw>
> argv[1] = <f2>
> argv[2] = <v^Aw>
> argv[1] = <a1>
> argv[2] = <uv^Aw>
> argv[1] = <a2>
> argv[2] = <uv^Aw>
> argv[1] = <a3>
> argv[2] = <uv^Aw>
> argv[1] = <a4>
> argv[2] = <uv^Aw>
> argv[1] = <e1>
> argv[2] = <uv^Aw>
> argv[1] = <e2>
> argv[2] = <uv^Aw>
> argv[1] = <d1>
> argv[2] = <^Aw>
> argv[1] = <d2>
> argv[2] = <^Aw>
> argv[1] = <@1>
> argv[2] = <uv^Aw^Axy>
> argv[3] = <uv^Aw^Axy>
> argv[1] = <@2>
> argv[2] = <uv^Aw^Axy>
> argv[3] = <uv^Aw^Axy>
> argv[1] = <aa1>
> argv[2] = <uv^A^A>
> argv[1] = <aa2>
> argv[2] = <uv^A^A>
> argv[1] = <aa3>
> argv[2] = <uv^A^Awx>
> argv[3] = <uv^A^Awx>
> argv[1] = <aa4>
> argv[2] = <uv^A^Awx>
> argv[3] = <uv^A^Awx>
run-nquote2
1,56c1,76
< ./nquote2.tests: line 18: recho: command not found
< ./nquote2.tests: line 19: recho: command not found
< ./nquote2.tests: line 21: recho: command not found
< ./nquote2.tests: line 22: recho: command not found
< ./nquote2.tests: line 23: recho: command not found
< ./nquote2.tests: line 24: recho: command not found
< ./nquote2.tests: line 26: recho: command not found
< ./nquote2.tests: line 27: recho: command not found
< ./nquote2.tests: line 28: recho: command not found
< ./nquote2.tests: line 29: recho: command not found
< ./nquote2.tests: line 31: recho: command not found
< ./nquote2.tests: line 32: recho: command not found
< ./nquote2.tests: line 33: recho: command not found
< ./nquote2.tests: line 34: recho: command not found
< ./nquote2.tests: line 36: recho: command not found
< ./nquote2.tests: line 37: recho: command not found
< ./nquote2.tests: line 38: recho: command not found
< ./nquote2.tests: line 39: recho: command not found
< ./nquote2.tests: line 45: recho: command not found
< ./nquote2.tests: line 46: recho: command not found
< ./nquote2.tests: line 47: recho: command not found
< ./nquote2.tests: line 48: recho: command not found
< ./nquote2.tests: line 50: recho: command not found
< ./nquote2.tests: line 51: recho: command not found
< ./nquote2.tests: line 52: recho: command not found
< ./nquote2.tests: line 53: recho: command not found
< ./nquote2.tests: line 58: recho: command not found
< ./nquote2.tests: line 59: recho: command not found
< ./nquote2.tests: line 61: recho: command not found
< ./nquote2.tests: line 62: recho: command not found
< ./nquote2.tests: line 63: recho: command not found
< ./nquote2.tests: line 64: recho: command not found
< ./nquote2.tests: line 66: recho: command not found
< ./nquote2.tests: line 67: recho: command not found
< ./nquote2.tests: line 68: recho: command not found
< ./nquote2.tests: line 69: recho: command not found
< ./nquote2.tests: line 71: recho: command not found
< ./nquote2.tests: line 72: recho: command not found
< ./nquote2.tests: line 73: recho: command not found
< ./nquote2.tests: line 74: recho: command not found
< ./nquote2.tests: line 76: recho: command not found
< ./nquote2.tests: line 77: recho: command not found
< ./nquote2.tests: line 78: recho: command not found
< ./nquote2.tests: line 79: recho: command not found
< ./nquote2.tests: line 81: recho: command not found
< ./nquote2.tests: line 82: recho: command not found
< ./nquote2.tests: line 84: recho: command not found
< ./nquote2.tests: line 85: recho: command not found
< ./nquote2.tests: line 86: recho: command not found
< ./nquote2.tests: line 87: recho: command not found
< ./nquote2.tests: line 89: recho: command not found
< ./nquote2.tests: line 90: recho: command not found
< ./nquote2.tests: line 92: recho: command not found
< ./nquote2.tests: line 93: recho: command not found
< ./nquote2.tests: line 94: recho: command not found
< ./nquote2.tests: line 95: recho: command not found
---
> argv[1] = <a^Ab>
> argv[1] = <uv^A^Awx>
> argv[1] = <aAb>
> argv[1] = <aAb>
> argv[1] = <uvA^Awx>
> argv[1] = <uvA^Awx>
> argv[1] = <a^AB>
> argv[1] = <a^AB>
> argv[1] = <uv^A^AWx>
> argv[1] = <uv^A^AWx>
> argv[1] = <aAb>
> argv[1] = <aAb>
> argv[1] = <uvAAwx>
> argv[1] = <uvAAwx>
> argv[1] = <a^AB>
> argv[1] = <a^AB>
> argv[1] = <uv^A^AWx>
> argv[1] = <uv^A^AWx>
> argv[1] = <uvA^Awx>
> argv[2] = <uvA^Awx>
> argv[1] = <uvA^Awx>
> argv[2] = <uvA^Awx>
> argv[1] = <uv^A^AWx>
> argv[2] = <uv^A^AWx>
> argv[1] = <uv^A^AWx>
> argv[2] = <uv^A^AWx>
> argv[1] = <uvAAwx>
> argv[2] = <uvAAwx>
> argv[1] = <uvAAwx>
> argv[2] = <uvAAwx>
> argv[1] = <uv^A^AWx>
> argv[2] = <uv^A^AWx>
> argv[1] = <uv^A^AWx>
> argv[2] = <uv^A^AWx>
> argv[1] = <a^Ab>
> argv[1] = <uv^A^Awx>
> argv[1] = <aAb>
> argv[1] = <aAb>
> argv[1] = <uvA^Awx>
> argv[1] = <uvA^Awx>
> argv[1] = <a^AB>
> argv[1] = <a^AB>
> argv[1] = <uv^A^AWx>
> argv[1] = <uv^A^AWx>
> argv[1] = <aAb>
> argv[1] = <aAb>
> argv[1] = <uvAAwx>
> argv[1] = <uvAAwx>
> argv[1] = <a^AB>
