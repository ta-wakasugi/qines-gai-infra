# 日本語チェック

- ひらがな
- カタカナ
- 漢字

# Headers

x

```
# h1 Heading 8-)
## h2 Heading
### h3 Heading
#### h4 Heading
##### h5 Heading
###### h6 Heading

Alternatively, for H1 and H2, an underline-ish style:

Alt-H1
======

Alt-H2
------
```

# h1 Heading 8-)

## h2 Heading

### h3 Heading

#### h4 Heading

##### h5 Heading

###### h6 Heading

Alternatively, for H1 and H2, an underline-ish style:

# Alt-H1

## Alt-H2

---

# Emphasis

```
Emphasis, aka italics, with *asterisks* or _underscores_.

Strong emphasis, aka bold, with **asterisks** or __underscores__.

Combined emphasis with **asterisks and _underscores_**.

Strikethrough uses two tildes. ~~Scratch this.~~

**This is bold text**

__This is bold text__

*This is italic text*

_This is italic text_

~~Strikethrough~~
```

Emphasis, aka italics, with _asterisks_ or _underscores_.

Strong emphasis, aka bold, with **asterisks** or **underscores**.

Combined emphasis with **asterisks and _underscores_**.

Strikethrough uses two tildes. ~~Scratch this.~~

**This is bold text**

**This is bold text**

_This is italic text_

_This is italic text_

~~Strikethrough~~

---

# Lists

```
1. First ordered list item
2. Another item
⋅⋅* Unordered sub-list.
1. Actual numbers don't matter, just that it's a number
⋅⋅1. Ordered sub-list
4. And another item.

⋅⋅⋅You can have properly indented paragraphs within list items. Notice the blank line above, and the leading spaces (at least one, but we'll use three here to also align the raw Markdown).

⋅⋅⋅To have a line break without a paragraph, you will need to use two trailing spaces.⋅⋅
⋅⋅⋅Note that this line is separate, but within the same paragraph.⋅⋅
⋅⋅⋅(This is contrary to the typical GFM line break behaviour, where trailing spaces are not required.)

* Unordered list can use asterisks
- Or minuses
+ Or pluses

1. Make my changes
    1. Fix bug
    2. Improve formatting
        - Make the headings bigger
2. Push my commits to GitHub
3. Open a pull request
    * Describe my changes
    * Mention all the members of my team
        * Ask for feedback

+ Create a list by starting a line with `+`, `-`, or `*`
+ Sub-lists are made by indenting 2 spaces:
  - Marker character change forces new list start:
    * Ac tristique libero volutpat at
    + Facilisis in pretium nisl aliquet
    - Nulla volutpat aliquam velit
+ Very easy!
```

1. First ordered list item
2. Another item
   ⋅⋅\* Unordered sub-list.
3. Actual numbers don't matter, just that it's a number
   ⋅⋅1. Ordered sub-list
4. And another item.

⋅⋅⋅You can have properly indented paragraphs within list items. Notice the blank line above, and the leading spaces (at least one, but we'll use three here to also align the raw Markdown).

⋅⋅⋅To have a line break without a paragraph, you will need to use two trailing spaces.⋅⋅
⋅⋅⋅Note that this line is separate, but within the same paragraph.⋅⋅
⋅⋅⋅(This is contrary to the typical GFM line break behaviour, where trailing spaces are not required.)

- Unordered list can use asterisks

* Or minuses

- Or pluses

1. Make my changes
   1. Fix bug
   2. Improve formatting
      - Make the headings bigger
2. Push my commits to GitHub
3. Open a pull request
   - Describe my changes
   - Mention all the members of my team
     - Ask for feedback

- Create a list by starting a line with `+`, `-`, or `*`
- Sub-lists are made by indenting 2 spaces:
  - Marker character change forces new list start:
    - Ac tristique libero volutpat at
    * Facilisis in pretium nisl aliquet
    - Nulla volutpat aliquam velit
- Very easy!

---

# Task lists

```
- [x] Finish my changes
- [ ] Push my commits to GitHub
- [ ] Open a pull request
- [x] @mentions, #refs, [links](), **formatting**, and <del>tags</del> supported
- [x] list syntax required (any unordered or ordered list supported)
- [x] this is a complete item
- [ ] this is an incomplete item
```

- [x] Finish my changes
- [ ] Push my commits to GitHub
- [ ] Open a pull request
- [x] @mentions, #refs, [links](), **formatting**, and <del>tags</del> supported
- [x] list syntax required (any unordered or ordered list supported)
- [ ] this is a complete item
- [ ] this is an incomplete item

---

# Ignoring Markdown formatting

You can tell GitHub to ignore (or escape) Markdown formatting by using \ before the Markdown character.

```
Let's rename \*our-new-project\* to \*our-old-project\*.
```

Let's rename \*our-new-project\* to \*our-old-project\*.

---

# Links

```
[I'm an inline-style link](https://www.google.com)

[I'm an inline-style link with title](https://www.google.com "Google's Homepage")

[I'm a reference-style link][Arbitrary case-insensitive reference text]

[I'm a relative reference to a repository file](../blob/master/LICENSE)

[You can use numbers for reference-style link definitions][1]

Or leave it empty and use the [link text itself].

URLs and URLs in angle brackets will automatically get turned into links.
http://www.example.com or <http://www.example.com> and sometimes
example.com (but not on Github, for example).

Some text to show that the reference links can follow later.

[arbitrary case-insensitive reference text]: https://www.mozilla.org
[1]: http://slashdot.org
[link text itself]: http://www.reddit.com
```

[I'm an inline-style link](https://www.google.com)

[I'm an inline-style link with title](https://www.google.com "Google's Homepage")

[I'm a reference-style link][Arbitrary case-insensitive reference text]

[I'm a relative reference to a repository file](../blob/master/LICENSE)

[You can use numbers for reference-style link definitions][1]

Or leave it empty and use the [link text itself].

URLs and URLs in angle brackets will automatically get turned into links.
http://www.example.com or <http://www.example.com> and sometimes
example.com (but not on Github, for example).

Some text to show that the reference links can follow later.

[arbitrary case-insensitive reference text]: https://www.mozilla.org
[1]: http://slashdot.org
[link text itself]: http://www.reddit.com

---

# Images

```
Here's our logo (hover to see the title text):

Inline-style:
![alt text](https://github.com/adam-p/markdown-here/raw/master/src/common/images/icon48.png "Logo Title Text 1")

Reference-style:
![alt text][logo]

[logo]: https://github.com/adam-p/markdown-here/raw/master/src/common/images/icon48.png "Logo Title Text 2"

![Minion](https://octodex.github.com/images/minion.png)
![Stormtroopocat](https://octodex.github.com/images/stormtroopocat.jpg "The Stormtroopocat")

Like links, Images also have a footnote style syntax

![Alt text][id]

With a reference later in the document defining the URL location:

[id]: https://octodex.github.com/images/dojocat.jpg  "The Dojocat"
```

Here's our logo (hover to see the title text):

Inline-style:
![alt text](https://github.com/adam-p/markdown-here/raw/master/src/common/images/icon48.png "Logo Title Text 1")

Reference-style:
![alt text][logo]

[logo]: https://github.com/adam-p/markdown-here/raw/master/src/common/images/icon48.png "Logo Title Text 2"

![Minion](https://octodex.github.com/images/minion.png)
![Stormtroopocat](https://octodex.github.com/images/stormtroopocat.jpg "The Stormtroopocat")

Like links, Images also have a footnote style syntax

![Alt text][id]

With a reference later in the document defining the URL location:

[id]: https://octodex.github.com/images/dojocat.jpg "The Dojocat"

---

# [Footnotes](https://github.com/markdown-it/markdown-it-footnote)

```
Footnote 1 link[^first].

Footnote 2 link[^second].

Inline footnote^[Text of inline footnote] definition.

Duplicated footnote reference[^second].

[^first]: Footnote **can have markup**

    and multiple paragraphs.

[^second]: Footnote text.
```

Footnote 1 link[^first].

Footnote 2 link[^second].

Inline footnote^[Text of inline footnote] definition.

Duplicated footnote reference[^second].

[^first]: Footnote **can have markup**

    and multiple paragraphs.

[^second]: Footnote text.

---

# Code and Syntax Highlighting

```
Inline `code` has `back-ticks around` it.
```

Inline `code` has `back-ticks around` it.

```c#
using System.IO.Compression;

#pragma warning disable 414, 3021

namespace MyApplication
{
    [Obsolete("...")]
    class Program : IInterface
    {
        public static List<int> JustDoIt(int count)
        {
            Console.WriteLine($"Hello {Name}!");
            return new List<int>(new int[] { 1, 2, 3 })
        }
    }
}
```

```css
@font-face {
  font-family: Chunkfive;
  src: url("Chunkfive.otf");
}

body,
.usertext {
  color: #f0f0f0;
  background: #600;
  font-family: Chunkfive, sans;
}

@import url(print.css);
@media print {
  a[href^="http"]::after {
    content: attr(href);
  }
}
```

```javascript
function $initHighlight(block, cls) {
  try {
    if (cls.search(/\bno\-highlight\b/) != -1)
      return process(block, true, 0x0F) +
             ` class="${cls}"`;
  } catch (e) {
    /* handle exception */
  }
  for (var i = 0 / 2; i < classes.length; i++) {
    if (checkCondition(classes[i]) === undefined)
      console.log('undefined');
  }
}

export  $initHighlight;
```

```php
require_once 'Zend/Uri/Http.php';

namespace Location\Web;

interface Factory
{
    static function _factory();
}

abstract class URI extends BaseURI implements Factory
{
    abstract function test();

    public static $st1 = 1;
    const ME = "Yo";
    var $list = NULL;
    private $var;

    /**
     * Returns a URI
     *
     * @return URI
     */
    static public function _factory($stats = array(), $uri = 'http')
    {
        echo __METHOD__;
        $uri = explode(':', $uri, 0b10);
        $schemeSpecific = isset($uri[1]) ? $uri[1] : '';
        $desc = 'Multi
line description';

        // Security check
        if (!ctype_alnum($scheme)) {
            throw new Zend_Uri_Exception('Illegal scheme');
        }

        $this->var = 0 - self::$st;
        $this->list = list(Array("1"=> 2, 2=>self::ME, 3 => \Location\Web\URI::class));

        return [
            'uri'   => $uri,
            'value' => null,
        ];
    }
}

echo URI::ME . URI::$st1;

__halt_compiler () ; datahere
datahere
datahere */
datahere
```

---

# Tables

```
Colons can be used to align columns.

| Tables        | Are           | Cool  |
| ------------- |:-------------:| -----:|
| col 3 is      | right-aligned | $1600 |
| col 2 is      | centered      |   $12 |
| zebra stripes | are neat      |    $1 |

There must be at least 3 dashes separating each header cell.
The outer pipes (|) are optional, and you don't need to make the
raw Markdown line up prettily. You can also use inline Markdown.

Markdown | Less | Pretty
--- | --- | ---
*Still* | `renders` | **nicely**
1 | 2 | 3

| First Header  | Second Header |
| ------------- | ------------- |
| Content Cell  | Content Cell  |
| Content Cell  | Content Cell  |

| Command | Description |
| --- | --- |
| git status | List all new or modified files |
| git diff | Show file differences that haven't been staged |

| Command | Description |
| --- | --- |
| `git status` | List all *new or modified* files |
| `git diff` | Show file differences that **haven't been** staged |

| Left-aligned | Center-aligned | Right-aligned |
| :---         |     :---:      |          ---: |
| git status   | git status     | git status    |
| git diff     | git diff       | git diff      |

| Name     | Character |
| ---      | ---       |
| Backtick | `         |
| Pipe     | \|        |
```

Colons can be used to align columns.

| Tables        |      Are      |  Cool |
| ------------- | :-----------: | ----: |
| col 3 is      | right-aligned | $1600 |
| col 2 is      |   centered    |   $12 |
| zebra stripes |   are neat    |    $1 |

There must be at least 3 dashes separating each header cell.
The outer pipes (|) are optional, and you don't need to make the
raw Markdown line up prettily. You can also use inline Markdown.

| Markdown | Less      | Pretty     |
| -------- | --------- | ---------- |
| _Still_  | `renders` | **nicely** |
| 1        | 2         | 3          |

| First Header | Second Header |
| ------------ | ------------- |
| Content Cell | Content Cell  |
| Content Cell | Content Cell  |

| Command    | Description                                    |
| ---------- | ---------------------------------------------- |
| git status | List all new or modified files                 |
| git diff   | Show file differences that haven't been staged |

| Command      | Description                                        |
| ------------ | -------------------------------------------------- |
| `git status` | List all _new or modified_ files                   |
| `git diff`   | Show file differences that **haven't been** staged |

| Left-aligned | Center-aligned | Right-aligned |
| :----------- | :------------: | ------------: |
| git status   |   git status   |    git status |
| git diff     |    git diff    |      git diff |

| Name     | Character |
| -------- | --------- |
| Backtick | `         |
| Pipe     | \|        |

---

# Blockquotes

```
> Blockquotes are very handy in email to emulate reply text.
> This line is part of the same quote.

Quote break.

> This is a very long line that will still be quoted properly when it wraps. Oh boy let's keep writing to make sure this is long enough to actually wrap for everyone. Oh, you can *put* **Markdown** into a blockquote.

> Blockquotes can also be nested...
>> ...by using additional greater-than signs right next to each other...
> > > ...or with spaces between arrows.
```

> Blockquotes are very handy in email to emulate reply text.
> This line is part of the same quote.

Quote break.

> This is a very long line that will still be quoted properly when it wraps. Oh boy let's keep writing to make sure this is long enough to actually wrap for everyone. Oh, you can _put_ **Markdown** into a blockquote.

> Blockquotes can also be nested...
>
> > ...by using additional greater-than signs right next to each other...
> >
> > > ...or with spaces between arrows.

---

# Inline HTML

```
<dl>
  <dt>Definition list</dt>
  <dd>Is something people use sometimes.</dd>

  <dt>Markdown in HTML</dt>
  <dd>Does *not* work **very** well. Use HTML <em>tags</em>.</dd>
</dl>
```

<dl>
  <dt>Definition list</dt>
  <dd>Is something people use sometimes.</dd>

  <dt>Markdown in HTML</dt>
  <dd>Does *not* work **very** well. Use HTML <em>tags</em>.</dd>
</dl>

---

# Horizontal Rules

```
Three or more...

---

Hyphens

***

Asterisks

___

Underscores
```

Three or more...

---

Hyphens

---

Asterisks

---

Underscores

---

# YouTube Videos

```
<a href="http://www.youtube.com/watch?feature=player_embedded&v=YOUTUBE_VIDEO_ID_HERE" target="_blank">
<img src="http://img.youtube.com/vi/YOUTUBE_VIDEO_ID_HERE/0.jpg" alt="IMAGE ALT TEXT HERE" width="240" height="180" border="10">
</a>
```

<a href="http://www.youtube.com/watch?feature=player_embedded&v=YOUTUBE_VIDEO_ID_HERE" target="_blank">
<img src="http://img.youtube.com/vi/YOUTUBE_VIDEO_ID_HERE/0.jpg" alt="IMAGE ALT TEXT HERE" width="240" height="180" border="10">
</a>

```
[![IMAGE ALT TEXT HERE](http://img.youtube.com/vi/YOUTUBE_VIDEO_ID_HERE/0.jpg)](http://www.youtube.com/watch?v=YOUTUBE_VIDEO_ID_HERE)
```

[![IMAGE ALT TEXT HERE](https://upload.wikimedia.org/wikipedia/commons/thumb/e/ef/YouTube_logo_2015.svg/1200px-YouTube_logo_2015.svg.png)](https://www.youtube.com/watch?v=ciawICBvQoE)

---

## Base64 encoded Image

![sample](data:image/jpeg;base64,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)
