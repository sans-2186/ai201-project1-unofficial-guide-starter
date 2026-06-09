# Project 1 Planning: The Unofficial Guide

> Write this document before you write any pipeline code.
> Your spec and architecture diagram are what you'll use to direct AI tools (Claude, Copilot, etc.) to generate your implementation — the more specific they are, the more useful the generated code will be.
> Update the Retrieval Approach and Chunking Strategy sections if you change your approach during implementation.
> Update this file before starting any stretch features.

---

## Domain

<!-- What domain did you choose? Why is this knowledge valuable and hard to find through official channels? -->
The domain I chose is "Rate my Schedule". I've seen many students, especially freshmen and sophomores, ask other students about professors and courses on reddit. Even though it's considered best to ask the academic advisior. However, most advisors are either busy or they vaguely give valid criticism about professors and compatibilty of courses taken in a particular semester. It is also hard to reach out to advisors after the courses are decided. 

---

## Documents

<!-- List your specific sources: URLs, subreddit names, forum threads, or file descriptions.
     Aim for at least 10 sources that together cover different subtopics or perspectives within your domain. -->

| # | Source | Description | URL or location |
|---|--------|-------------|-----------------|
| 1 | Reddit | A science major rushing to lock in classes last-minute and asking if it's doable | https://www.reddit.com/r/utdallas/comments/185osys/rate_my_schedule/ |
| 2 | Reddit | A CS major asking which professors to take for sophomore-level courses | https://www.reddit.com/r/utdallas/comments/1smfx3i/rate_my_schedule/ |
| 3 | Reddit | A freshman switching from communications to business, checking if their plan still fits | https://www.reddit.com/r/utdallas/comments/1ty55ls/rate_my_schedule_pleaseee/ |
| 4 | Reddit | A new CS transfer asking how their first UTD semester looks | https://www.reddit.com/r/utdallas/comments/1ty80gg/rate_my_schedule_i_just_transferred_to_utd_and/ |
| 5 | Reddit | A neuroscience honors student asking if the extra workload is manageable | https://www.reddit.com/r/utdallas/comments/1tpoc5c/rate_my_schedule/ |
| 6 | Reddit | An IT major stacking 3000- and 4000-level courses, asking if it's too much | https://www.reddit.com/r/utdallas/comments/1sh476s/rate_my_schedule/ |
| 7 | Reddit | A mechanical engineering major wanting a gut check on their course load | https://www.reddit.com/r/utdallas/comments/1oogjgc/advice_onrate_my_schedule/ |
| 8 | Reddit | A pre-med bio major asking how to balance heavy labs without hurting their GPA | https://www.reddit.com/r/utdallas/comments/1ty9gj7/hows_my_schedule_premed/ |
| 9 | Reddit | A biochem major with an education minor planning a realistic Fall 2025 schedule | https://www.reddit.com/r/utdallas/comments/1kxsvha/rate_my_schedule_for_fall_2025/ |
| 10 | Reddit | A CS freshman asking if their first-semester intro load is a good start | https://www.reddit.com/r/utdallas/comments/1otwy7f/rate_my_schedule/ |

---

## Chunking Strategy

<!-- How will you split documents into chunks?
     State your chunk size (in tokens or characters), overlap size, and explain why those
     numbers fit the structure of your documents.
     A review-heavy corpus warrants different chunking than a long FAQ. -->

**Chunk size:** ~600 characters (roughly 150 tokens)

**Overlap:** ~100 characters (about one sentence)

**Reasoning:** My documents are short Reddit threads — a student posts their major and class list, and other students comment back. Each comment is usually one self-contained opinion, so I'm keeping chunks small so that one chunk holds roughly one person's advice instead of mashing five people together. 600 characters also stays under the 256-token limit of my embedding model so nothing gets cut off. The small overlap just keeps advice from getting split in half at the edge of a chunk. Before chunking I clean out the Reddit junk (vote counts, "Reply", timestamps) so the embeddings focus on what students actually said.

---

## Retrieval Approach

<!-- Which embedding model are you using (e.g., all-MiniLM-L6-v2 via sentence-transformers)?
     How many chunks will you retrieve per query (top-k)?
     If you were deploying this for real users and cost wasn't a constraint, what tradeoffs
     would you weigh in choosing a different embedding model — context length, multilingual
     support, accuracy on domain-specific text, latency? -->

**Embedding model:** `all-MiniLM-L6-v2` via sentence-transformers

**Top-k:** 5

**Production tradeoff reflection:** I picked all-MiniLM-L6-v2 because it's free, runs locally, and works well on short conversational text like Reddit comments. I went with top-5 since a schedule question usually has a few students agreeing or disagreeing, so I want a handful of opinions but not so many that off-topic stuff sneaks in.

If cost wasn't a problem and this was a real tool, I'd think about a bigger model like OpenAI's `text-embedding-3-large`. It would tell similar course numbers apart better (CS 2305 vs CS 2336) and handle the slang students use. It also allows longer inputs, so I could embed a whole thread at once instead of tiny chunks. The downside is it's an API call, so it costs money and adds a little delay. For this project that's not worth it, so MiniLM is the right fit.

---

## Evaluation Plan

<!-- List your 5 test questions with their expected correct answers.
     Questions should be specific enough that you can judge whether the system's response
     is right or wrong. "What are good dining halls?" is too vague.
     "What do students say about wait times at [dining hall name] during lunch?" is testable. -->

| # | Question | Expected answer |
|---|----------|-----------------|
| 1 | What do students say about taking multiple 2000-level CS courses in the same semester? | Commenters generally warn it's a heavy load and advise spreading core CS courses out or pairing them with lighter electives. |
| 2 | What advice did students give the transfer student who just came to UTD as a CS major? | Feedback on which transferred courses overlap, which professors to take, and that a first transfer semester shouldn't be overloaded while adjusting. |
| 3 | What do students recommend for a pre-med biology major's schedule? | Advice to balance heavy science/lab courses with GPA in mind, and warnings about combining certain demanding science courses in one term. |
| 4 | Is it manageable to take both 3000- and 4000-level IT courses together? | Students give a mixed but largely cautionary view, noting upper-level course workload and recommending checking professor difficulty before committing. |
| 5 | What do students think about a neuroscience major taking an honors course load? | Honors adds workload; commenters weigh whether the schedule leaves enough time and suggest dropping or rebalancing if it looks too dense. |

---

## Anticipated Challenges

<!-- What could go wrong? Name at least two specific risks with reasoning.
     Consider: noisy or inconsistent documents, missing source attribution, off-topic
     retrieval, chunks that split key information across boundaries. -->

1. **Students give opposite advice.** One person says a course combo is fine, another says it wrecked them, because their majors and workloads are different. If retrieval grabs both without the context of who said it, the system might make it sound like everyone agrees. I'll try to keep each post's major and year attached to its comments so that context isn't lost.

2. **Threads look too similar to each other.** Every post is called "Rate my Schedule" and uses the same words (course numbers, "load," "professor"), so a biology question might accidentally pull chunks from a CS thread. Reddit also has jokes and off-topic replies that aren't real advice. I'll clean out the junk and keep major/course info in each chunk so the search has enough to tell threads apart.

---

## Architecture

<!-- Draw a diagram of your pipeline showing the five stages:
     Document Ingestion → Chunking → Embedding + Vector Store → Retrieval → Generation
     Label each stage with the tool or library you're using.
     You can use ASCII art, a Mermaid diagram, or embed a sketch as an image.
     You'll use this diagram as context when prompting AI tools to implement each stage. -->

```
 Ingestion  -->   Chunking   -->  Embedding +   -->  Retrieval  -->  Generation
                                  Vector Store

 read .txt    clean Reddit      all-MiniLM-L6-v2   embed question,   send chunks +
 files from   junk, split       embeds chunks,     pull top-5        question to Groq,
 documents/   into ~600-char    stored in          closest chunks    show answer +
 (Python)     chunks, 100       ChromaDB           from ChromaDB     sources in a
              overlap                                                 simple UI
```

---

## AI Tool Plan

<!-- For each part of the pipeline below, describe:
     - Which AI tool you plan to use (Claude, Copilot, ChatGPT, etc.)
     - What you'll give it as input (which sections of this planning.md, which requirements)
     - What you expect it to produce
     - How you'll verify the output matches your spec

     "I'll use AI to help me code" is not a plan.
     "I'll give Claude my Chunking Strategy section and ask it to implement chunk_text()
     with my specified chunk size and overlap" is a plan. -->

**Milestone 3 — Ingestion and chunking:**

**Milestone 4 — Embedding and retrieval:**

**Milestone 5 — Generation and interface:**
