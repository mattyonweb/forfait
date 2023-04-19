# Forfait

A concatenative, strongly-typed programming language implemented in Python.

The goal is to write a compiler for Forfait capable of generating binaries for the Z80 (and maybe other architectures).

## Overview of the language

The language is heavily inspired by Forth and Cat. 

The syntax strives to be as minimal as possible without being too idealistic about it. 

An example program may be:

```
: square dup *8bit ;

0 10 [| square |] indexed-iter

:s
```

This program firstly defines a function named `square` on 8bit numbers; the function has signature `(''S U8 -> ''S U8)` (more on types later), and is delimited by `: (...) ;` as in Forth.

Then, `indexed-iter` executes the function `square` for each number between `0` and `9` (the weird parenthesis around `square` is a quotation, or a "suspended computation" if you prefer).

Finally, `:s` prints the stack on the screen.

## Type system

At the moment, the type system is only roughly sketched. 

There are two types of generics: classic generics and "Row" (or stack) generics; the latter allow to remain generic over a row (read: an ordered list) of types, instead than on only one type. 

Row generics are necessary if we want to correctly type `eval`-like functions. 

To see an example of this, let's first look at the "type signature" of a quotation.

Let's take the builtin function `drop` (the following syntax is only for sake of clarity, it is not the actual syntax of the language):

`drop :: (''S 'T -> ''S)`

The signature means: drop accepts whatever stack `''S` on top an object with generic type `'T`. Here `''S` is the row-generic variable, `'T` is a "classic" generic instead.

`[| drop |] :: (''R -> ''R (''S 'T -> ''S))`

The quotation (i.e. weird parenthesis) around `drop` wraps `drop` within a no-argument function: this is the way to delay the actual esecution of `drop` which, without the quotes, would be executed instantly. Note the existence of two row generics at the same time!

`eval :: (''U (''U -> ''V) -> ''V)`

With `eval` we can evaluate these "suspended computation" at our convenience. So for example, if we manually typecheck `[| drop |] eval`:

```
[| drop |]      :: (''R -> ''R (''S 'T -> ''S))
eval            ::        (''U (''U    -> ''V)  -> ''V)
                           ^^^  ^^^^^^    ^^^  
            ---------------------------------------
[| drop |] eval :: (''R -> ''V)  which, after unification, becomes:
[| drop |] eval :: (''S 'T -> ''S)  (names may be different IRL)
           
```

## Few examples

### Fibonacci

```
: fibonacci (( n -- fact(n) ))
  1 1

    [| rot- dup 1 >=u8 |]  (( checks if n still >= 1 ))
    [| --u8 rot+           (( decrements n and puts it in third position ))
       over +u8 swap |]    (( fib(n-1) fib(n-2) -- fib(n) fib(n-1) ))
  while

  drop drop
;

8 fibonacci :s     (( will print [55] ))
```

## TODOs

- [ ] Typing for recursive functions
- [ ] Syntax for explicit type annotations
- [ ] Structure-like data types
- [ ] Macro `declare` for defining constructors and accessor to typed variables
  - [ ] Use `declare` inside a funcdef for "local" variables is impossible, because that would require the concept of "scope" and i don't want it >:|