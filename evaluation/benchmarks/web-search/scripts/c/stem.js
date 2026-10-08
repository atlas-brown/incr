#!/usr/bin/env node

/*
Convert each term to its stem
Usage: ./stem.js <input >output
*/

const readline = require('readline');
// Import only the stemmer: the aggregate module initializes storage adapters
// whose dotenv diagnostics corrupt this program's stdout data stream.
const PorterStemmer = require('natural/lib/natural/stemmers/porter_stemmer');

const rl = readline.createInterface({
  input: process.stdin,
  output: process.stdout,
  terminal: false,
});

rl.on('line', function(line) {
  // Print the Porter stem from `natural` for each element of the stream.
  // __start_solution__
  console.log(PorterStemmer.stem(line));
  // __end_solution__
});
