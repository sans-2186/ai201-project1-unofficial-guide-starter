# Project 1 Planning: The Unofficial Guide

> Write this document before you write any pipeline code.
> Your spec and architecture diagram are what you'll use to direct AI tools (Claude, Copilot, etc.) to generate your implementation — the more specific they are, the more useful the generated code will be.
> Update the Retrieval Approach and Chunking Strategy sections if you change your approach during implementation.
> Update this file before starting any stretch features.

---

## Domain

<!-- What domain did you choose? Why is this knowledge valuable and hard to find through official channels? -->
The domain I chose is "Rate my Schedule". I've seen many students, especially freshmen and sophomores, ask other students about professors and courses on Reddit. Even though it's considered best to ask the academic advisor, most advisors are either busy or only vaguely comment on professors and the compatibility of courses taken in a particular semester. It is also harder to reach out to advisors after the courses are decided. Hence, communicating with other students and taking advice on a schedule is what I want to automate — something that isn't done officially but is currently widely used.

---

## Documents

<!-- List your specific sources: URLs, subreddit names, forum threads, or file descriptions.
     Aim for at least 10 sources that together cover different subtopics or perspectives within your domain. -->

| # | Source | Description | URL or location |
|---|--------|-------------|-----------------|
| 1 | Reddit | A science major rushing to lock in classes last-minute and asking if it's doable | https://www.reddit.com/r/utdallas/comments/185osys/rate_my_schedule/ |
| 2 | Reddit | A CS major asking which professors to take for sophomore-level courses | https://www.reddit.com/r/utdallas/comments/1smfx3i/rate_my_schedule/ |
| 3 | Reddit | A freshman switching from communications to business marketing, checking if their plan still fits | https://www.reddit.com/r/utdallas/comments/1ty55ls/rate_my_schedule_pleaseee/ |
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

**Overlap:** ~50 characters 

**Final chunk count:** 68 chunks across 10 documents (between the 50–2,000 range). Only the helpful, informative comments from the students are embedded. The original posts are the OP asking for help, like the app's user, so embedding them would only help with filtering the major and documents. Each course schedule, major, classification, and semester is kept as chunk metadata instead of embedding it as a standalone chunk, since a timetable carries no opinion to retrieve.

**Reasoning:** My documents are short conversational Reddit threads. Each comment is usually one self-contained opinion, so I'm keeping chunks small so that one chunk holds roughly one person's advice instead of mashing five people together. 600 characters also stays under the 256-token limit of my embedding model so nothing gets cut off. The small overlap just keeps advice from getting split in half at the edge of a chunk. Before chunking I clean out the Reddit junk (vote counts, "Reply", timestamps, datestamps) so the embeddings focus on what students actually said.

---

## Retrieval Approach

<!-- Which embedding model are you using (e.g., all-MiniLM-L6-v2 via sentence-transformers)?
     How many chunks will you retrieve per query (top-k)?
     If you were deploying this for real users and cost wasn't a constraint, what tradeoffs
     would you weigh in choosing a different embedding model — context length, multilingual
     support, accuracy on domain-specific text, latency? -->

**Embedding model:** `all-MiniLM-L6-v2` via sentence-transformers

**Top-k:** 5

**Production tradeoff reflection:** I picked all-MiniLM-L6-v2 because it's free, runs locally, and works well on short conversational text like Reddit comments. I went with top-5 since a schedule question usually has a few students agreeing or disagreeing, so I want a handful of opinions but not so many that off-topic stuff sneaks in. I think there are better paid models that would be easier to work with and are smarter when dealing with this kind of data.

---

## Evaluation Plan

<!-- List your 5 test questions with their expected correct answers.
     Questions should be specific enough that you can judge whether the system's response
     is right or wrong. "What are good dining halls?" is too vague.
     "What do students say about wait times at [dining hall name] during lunch?" is testable. -->


| # | Type | Question | Expected answer |
|---|------|----------|-----------------|
| 1 | Broad | What do students say about taking multiple 2000-level CS courses in the same semester? | A heavy but doable load; advice to load up early but lessen the gaps and spread core courses out. |
| 2 | Specific | Should I take Nhut Nguyen or Alice Wang for CS 2340 Computer Architecture? | Wang is recommended (structured class, an A is achievable with effort); Nguyen is poorly reviewed. Comp arch is hard regardless of professor. |
| 3 | Specific | What course sequence do students recommend for a pre-med student (gen chem, bio, ochem, biochem)? | A gated sequence: gen chem 1 → 2, take bio 2 before bio 1, finish gen chem + bio 2 before A&P, then ochem unlocks biochem. |
| 4 | Specific | What do students think of Professor Schulze for HIST 1301? | Mixed — several warn he has bad reviews and waited to avoid him; others (e.g. GoldyChoke, Comet7777) liked him. The Friday section can be a different professor. |
| 5 | Broad | Is it manageable to take both 3000- and 4000-level IT courses together? | A largely cautionary view on upper-level workload. Note: this thread is mostly professor reviews, so the corpus has limited direct "manageability" advice — an intentional coverage gap. |

---

## Anticipated Challenges

<!-- What could go wrong? Name at least two specific risks with reasoning.
     Consider: noisy or inconsistent documents, missing source attribution, off-topic
     retrieval, chunks that split key information across boundaries. -->

1. Students often have varying opinions on the same schedule. This might cause confusion for the model. I have to make sure that the model communicates both sides when a relevant question is asked by the user. 

2. Some OP information is in the comments when communicating with other students, like taking online classes and starting to move early because they're a commuter. I have to make sure to include that as part of the user query and not the comments given as advice by other students.

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
 documents   into ~600-char    stored in          closest chunks    show answer +
               chunks, 50        ChromaDB           from ChromaDB     sources in a
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
- **Tool:** Claude (Claude Code) and the Google Gemini extension to access the Reddit links.
- **Input:** the Chunking Strategy and Documents sections above, the pipeline diagram, and my 10 cleaned `.txt` files. I'll ask it to implement `load_documents()` and `chunk_document()` matching my 600-char / 50-overlap spec and attaching the source filename as metadata.
- **Expect:** a `config.py` and an `ingest.py` that loads, lightly cleans, and chunks the documents into a list, plus information about the count and sample chunks.
- **Verify:** run `python ingest.py`, read 5 sample chunks, confirm each is a self-contained comment (not a fragment/HTML/empty), and ensure the total is in the 50–2,000 range.

**Milestone 4 — Embedding and retrieval:**
- **Tool:** Claude.
- **Input:** the Retrieval Approach section (all-MiniLM-L6-v2, top-5) and the diagram. I'll ask it to embed the chunks from `ingest.py` and store them in ChromaDB with metadata, and to write a `retrieve(query, k)` function returning the top-k chunks with distances and source info.
- **Expect:** an `embed.py` with `build_store()` and `retrieve()`, using cosine distance so scores are interpretable.
- **Verify:** run at least 3 evaluation-plan queries, print the returned chunks + distance scores, and confirm the top results are on-topic and from the right source (scores well below the 0.6–0.7 weak-match line).

**Milestone 5 — Generation and interface:**
- **Tool:** Claude.
- **Input:** the Retrieval Approach section, the diagram, and my grounding requirement (answer from retrieved context only, with programmatic source attribution). I'll ask it to wire Groq's `llama-3.3-70b-versatile` onto `retrieve()` and build a Gradio UI.
- **Expect:** a `query.py` with `ask(question)` returning `{answer, sources}` enforced by a strict grounding system prompt (refuse when context is insufficient), and an `app.py` Gradio interface.
- **Verify:** test 2–3 in-domain queries (answers traceable to retrieved chunks, sources cited) and 1 out-of-domain query (must refuse, not fabricate). Confirm sources are appended programmatically, not invented by the model.
