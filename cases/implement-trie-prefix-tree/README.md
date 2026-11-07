# Implement Trie (Prefix Tree)

[LeetCode 208](https://leetcode.com/problems/implement-trie-prefix-tree/) | Tries

**The problem.** Build a store of words that answers two questions: is this exact word stored, and does any stored word begin with this text? The check drives it with a list of operations and collects the answers.

**Signature here.** `solve(ops) -> list of bool. Each op is ("insert", word), ("search", word) or ("prefix", word).`

**The shape to notice.** Words that share a beginning share storage. Each letter is one step down a tree, so a lookup costs only the length of the word.

**The idea.** Use nested dictionaries, one level per letter, with a marker on the node where a word ends. Exact search needs the marker. A prefix question only needs the path to exist.

**Complexity.** O(L) per operation for a word of length L, and O(total letters stored) space. The slow machine scans every stored word for each question.

**How an AI answer to this would be checked.** Compare the list of answers against slow's. Short words over two letters mean one stored word is often the beginning of another. Run it with `python3 check.py implement-trie-prefix-tree --answer your_file.py`.

## Hunt the bugs first

`wrong.py` holds two wrong answers. Run `python3 check.py implement-trie-prefix-tree`, read the smallest failing input for each, and work out why before you open these.

<details>
<summary>The gut answer</summary>

Appearing inside a word is not the same as beginning it. The word "ba" contains "a" but does not begin with it, and this answer says yes.

</details>

<details>
<summary>The planted bug</summary>

`planted` is `fast.py` with one line changed. It has `out.append(found)` where the correct line is `out.append(found if op == "prefix" else found and "$" in node)`. This drops the end-of-word marker from the exact search, so a stored "ab" makes a search for "a" say yes. It is the classic trie mistake, and prefix questions still work.

</details>
