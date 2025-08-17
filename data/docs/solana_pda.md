# Solana Program Derived Addresses (PDAs)

A **Program Derived Address (PDA)** is a deterministic address generated from one or more seeds plus a program ID. PDAs do not have private keys; instead, a program can sign via `invoke_signed` using the same seeds.
