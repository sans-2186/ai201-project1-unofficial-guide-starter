# The Unofficial Guide — Project 1

A retrieval-augmented system that answers UT Dallas course/professor questions
using only real student opinions from r/utdallas "Rate my Schedule" threads.

**Pipeline:** `documents/*.txt` → chunk (`ingest.py`) → embed + ChromaDB (`embed.py`) → retrieve + grounded generation with Groq (`query.py`) → Gradio UI (`app.py`).

Run it: `pip3 install -r requirements.txt`, add your `GROQ_API_KEY` to `.env`, then `python3 app.py` → http://localhost:7860.

---

## Domain

The domain I chose is "Rate my Schedule". I've seen many students, especially freshmen and sophomores, ask other students about professors and courses on Reddit. Even though it's considered best to ask the academic advisor, most advisors are either busy or only vaguely comment on professors and the compatibility of courses taken in a particular semester. It is also harder to reach out to advisors after the courses are decided. Hence, communicating with other students and taking advice on a schedule is what I want to automate — something that isn't done officially but is currently widely used.

---

## Document Sources

10 r/utdallas "Rate my Schedule" threads were chosen to represent varying majors, classifications, and situations. They were mostly manually cleaned by removing Reddit junk like vote counts, "Reply", timestamps, and datestamps. The cleaned version is a .txt file that holds crucial information like source, URL, major, classification, semester, schedule (including total credit hours), the OP's post, comments, and replies.

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

**Chunk size:** ~600 characters (~150 tokens).

**Overlap:** ~50 characters 

**Why these choices fit your documents:** The documents mostly have short Reddit threads where each comment is one self-contained opinion. So instead of cutting every 600 characters (which split sentences mid-word and merged several commenters into one chunk), the chunker splits between comments — each top-level comment plus its nested replies stays in one chunk ("one chunk ≈ one person's advice"). Only a comment longer than 600 characters is split further, and then at sentence boundaries so pieces stay readable. 600 chars stays under the embedding model's 256-token limit. Some features are: (1) Posts are not embedded because the OP has a query, (2) Schedules are stored as metadata to only serve as context, and (3) A short `Context: <major>, <semester>.` line is added to each chunk so it's easier to filter based on major and semester.

**Final chunk count:** 68 chunks across 10 documents.

---

## Sample Chunks

Five representative chunks produced by `ingest.py` (`build_chunks()`), each labeled with its `chunk_id` and source document. Note the `Context: <major>, <semester>.` line prepended to every chunk and the OP-vs-commenter structure preserved inside a single chunk.

**1. `01_science_lastminute_0`** — source: `01_science_lastminute` (Science / pre-health, Spring 2023)
> Context: Science (pre-health), Spring 2023.
> - [WisCollin] The wide gap in the middle of the day is going to make every day feel really long, and it might be hard to stay focused in those evening sessions. Your Thursday is absolutely brutal. Physics and Chemistry with basically no break for like 9 hours… Only reason it's not worse is that the difficulty should be manageable and you have plenty of designated hours to study and make office hours during the days… This schedule sucks.

**2. `02_cs_sophomore_profs_0`** — source: `02_cs_sophomore_profs` (Computer Science, Fall 2026)
> Context: Computer Science, Fall 2026.
> - [Alert-Ad7097] Peak linear algebra prof, 2336 prof is good (easy A), everyday class is awful

**3. `03_comm_to_business_marketing_freshman_0`** — source: `03_comm_to_business_marketing_freshman` (Business Marketing, switching from Communications, Fall 2026)
> Context: Business Marketing (switching from Communications), Fall 2026.
> - [ThisIsntABadName] If you're changing your major to business marketing you will need to take BA 1104.
> - [OP] Oh okay so should I just take out BLAW then?
> - [OoRo0] No it's only a half semester class. I'm in marketing! lmk if you have any questions this looks good so far!

**4. `04_cs_transfer_first_sem_0`** — source: `04_cs_transfer_first_sem` (Computer Science transfer, Fall 2026)
> Context: Computer Science, Fall 2026.
> - [TemocOrionGalaxy] Why do you only have 10 credit hours? You're technically not a full-time student with that few credit hours.
> - [OP] I got ECS 2390 online.

**5. `05_neuroscience_honors_0`** — source: `05_neuroscience_honors` (Neuroscience honors, Fall 2026)
> Context: Neuroscience (honors), Fall 2026.
> - [SignificantShoe3088] …chem lab is gonna be rough that early in the morning, but I heard Huang is good. Also make sure to do the swap with waitlist just in case you get a good professor like Ladow for neuro.

---

## Embedding Model

**Model used:** `all-MiniLM-L6-v2` via `sentence-transformers`. It runs locally with no API key and no expenses, and it performs well on short, informal, conversational text like Reddit. Vectors are stored in a local **ChromaDB** collection using cosine distance, and queries retrieve the top-5 closest chunks.

**Production tradeoff reflection:** If cost weren't a constraint and this served real users, I'd use a larger model from OpenAI or Anthropic. It would distinguish similar course numbers better (CS 2305 vs CS 2336), handle student slang and abbreviations more smartly, and allow much longer inputs at once instead of smaller chunks. Such a model would be a great fit if this project were to scale campus-wide one day. However, for a 68-chunk personal project, MiniLM is the right fit.

---

## Retrieval Test Results

Three queries run through `retrieve(query, k=5)` (cosine distance — lower is closer; the system flags anything above ~0.6 as a weak match). Top-3 chunks shown per query.

**Query A — "What do students say about taking multiple 2000-level CS courses in the same semester?"**
| # | Distance | Source | Chunk (trimmed) |
|---|----------|--------|-----------------|
| 1 | 0.455 | `10_cs_freshman_intro` | "For a freshman CS/SE major its fine… better to load up in your first year so when you start taking the harder classes you can actually make a schedule that doesn't leave you swamped… Try to lessen the gaps though." |
| 2 | 0.497 | `10_cs_freshman_intro` | "That looks like hell. The big gaps between classes also seem like a good idea, but in reality they suck and are usually very unproductive." |
| 3 | 0.512 | `08_premed_bio_labs` | "Better to get some classes out sooner than later because you will be taking multiple science classes in the same semester afterwards…" |

**Query B — "Should I take Nhut Nguyen or Alice Wang for CS 2340 Computer Architecture?"**
| # | Distance | Source | Chunk (trimmed) |
|---|----------|--------|-----------------|
| 1 | 0.509 | `02_cs_sophomore_profs` | "That CS2340 is going to be tough… [OP] who do you reccomend alice or nhut? — Alice fs, you will learn the stuff and A is guaranteed if you put in the work." |
| 2 | 0.544 | `02_cs_sophomore_profs` | "Have heard some really bad things about Nguyen… I'm taking Wang. I've heard mixed things… A lot of people just said not to take comp arch at UTD." |
| 3 | 0.551 | `02_cs_sophomore_profs` | "alice wang was a very structured class, but I think its just in the nature of comp arch to be difficult overall, pretty good class and her slides worked well for me." |

**Query C — "What course sequence do students recommend for pre-med (gen chem, bio, ochem)?"**
| # | Distance | Source | Chunk (trimmed) |
|---|----------|--------|-----------------|
| 1 | 0.328 | `08_premed_bio_labs` | "After finishing gen chem u can take ochem, which THEN biochem is unlocked for u. Lots of classes are locked behind each other…" |
| 2 | 0.336 | `08_premed_bio_labs` | "your main progression… you are forced to do gen chem 1 → GC 2 (takes 2 semesters), and intro to bio 2 and bio 1… I recommend taking bio 2 then bio 1, because bio 1 requires gc 2 but bio 2 doesn't… finish gc 1 and 2, and bio 2, before a&p 1 and then 2." |
| 3 | 0.417 | `08_premed_bio_labs` | "[OP] …i need pre reqs for the rest… ill prob end up taking them in summer to get out of the way!!" |

**Why the returned chunks are relevant (Query B):** All three top chunks come from `02_cs_sophomore_profs`, the only thread that discusses CS 2340 professors by name, and the distances are tight (0.51–0.55). They directly answer the comparison: chunk 1 recommends Wang, chunk 2 reports negative reports on Nguyen, and chunk 3 corroborates Wang while noting comp arch is hard regardless. Retrieval landed exactly on the named-professor opinions the query asked for, not generic course-load chatter.

**Why the returned chunks are relevant (Query C):** The top two chunks have the lowest distances in the whole test set (0.328, 0.336), both from the pre-med bio thread, and they lay out the exact prerequisite chain the query asks about — gen chem 1→2, bio 2 before bio 1, ochem then biochem, A&P timing. The embedding model matched on the domain-specific course progression rather than just the words "pre-med," which is why these chunks support a precise, sequenced answer.

---

## Grounded Generation

**System prompt grounding instruction:** The model `llama-3.3-70b-versatile` on Groq only uses student comments and replies with "I don't have enough information on that." if the information is not embedded, instead of hallucinating and making information up. This also helped with summarizing varying student opinions while leaving the final decision to the user.

**How source attribution is surfaced in the response:** Attribution is programmatic, not left to the model. After retrieval, the system builds a deduplicated source list directly from the retrieved chunks' metadata (source document + real Reddit URL) and returns it alongside the answer. If the model refuses ("I don't have enough information…"), the source list is suppressed, since a refusal has no real sources to cite.

---

## Example Responses

Real output from `ask()` (Groq `llama-3.3-70b-versatile`, temperature 0). Sources are appended programmatically from chunk metadata.

**Example 1 — in domain (professor comparison)**
> **Q:** Should I take Nhut Nguyen or Alice Wang for CS 2340 Computer Architecture?
>
> **Answer:** Students say Nhut Nguyen is a "notoriously bad professor". In contrast, one commenter recommends Alice Wang, saying "you will learn the stuff and A is guaranteed if you put in the work". Another student found Alice Wang's class to be "very structured" and "pretty good". However, some students also mention that Computer Architecture is a difficult subject overall.
>
> **Sources:**
> - `02_cs_sophomore_profs` — https://www.reddit.com/r/utdallas/comments/1smfx3i/rate_my_schedule/
> - `06_it_3000_4000_stack` — https://www.reddit.com/r/utdallas/comments/1sh476s/rate_my_schedule/

**Example 2 — in domain (mixed-opinion professor)**
> **Q:** What do students think of Professor Schulze for HIST 1301?
>
> **Answer:** Students have mixed opinions about Professor Schulze. Some students say he is great, one commenter recommends him, and another student found his class not boring. However, one student warns that his class requires more effort than expected to do well, and another mentions that Schulze has "very very bad reviews" and they would be scared of getting a B in his class.
>
> **Sources:**
> - `03_comm_to_business_marketing_freshman` — https://www.reddit.com/r/utdallas/comments/1ty55ls/rate_my_schedule_pleaseee/
> - `07_mechanical_eng_load` — https://www.reddit.com/r/utdallas/comments/1oogjgc/advice_onrate_my_schedule/
> - `06_it_3000_4000_stack` — https://www.reddit.com/r/utdallas/comments/1sh476s/rate_my_schedule/

**Example 3 — out of scope (refusal)**
> **Q:** What's the best dining hall at UT Dallas?
>
> **Answer:** I don't have enough information on that.
>
> **Sources:** *(none — suppressed on refusal)*

The dining-hall query is outside the corpus (the threads are about courses and professors, not dining), so the model returns the exact refusal string and the pipeline shows no sources instead of citing irrelevant retrieved chunks.

---

## Query Interface

A single-question Gradio web app (`app.py`, served at `http://localhost:7860`).

**Input field**
- **Your question** (textbox) — a free-text course/professor question, e.g. *"Should I take Nhut Nguyen or Alice Wang for CS 2340?"* Three clickable example questions are provided. Submit with the **Ask** button or the Enter key. Empty input returns a "Please enter a question." prompt.

**Output fields**
- **Answer** (textbox, 8 lines) — the grounded answer, or the refusal string if the threads don't cover the question.
- **Retrieved from** (textbox, 4 lines) — the deduplicated source list (document + Reddit URL); shows "— (no matching student comments)" on a refusal.

**Sample interaction transcript**
```
Your question:  What course sequence do students recommend for pre-med (gen chem, bio, ochem)?

[Ask]

Answer:
Students recommend a gated sequence: finish gen chem 1 → gen chem 2 (two semesters),
and take intro to bio 2 before bio 1 (bio 1 requires gen chem 2, bio 2 doesn't). Finish
gen chem 1 & 2 and bio 2 before A&P 1, then A&P 2. After gen chem, ochem opens up, and
ochem then unlocks biochem. Students suggest getting A&P done early (TA perks) and not
overloading electives in heavy science semesters.

Retrieved from:
• 08_premed_bio_labs (https://www.reddit.com/r/utdallas/comments/1ty9gj7/hows_my_schedule_premed/)
```

---

## Evaluation Report

| # | Question | Expected answer | System response (summarized) | Retrieval quality | Response accuracy |
|---|----------|-----------------|------------------------------|-------------------|-------------------|
| 1 | What do students say about taking multiple 2000-level CS courses in the same semester? | Heavy but doable; load up early but lessen gaps. | "I don't have enough information on that." | Partially relevant | Inaccurate (over-refusal) |
| 2 | Should I take Nhut Nguyen or Alice Wang for CS 2340 Computer Architecture? | Wang recommended; Nguyen poorly reviewed; comp arch hard regardless. | Recommends Wang ("A is guaranteed if you put in the work", "very structured"); Nguyen "notoriously bad"; notes comp arch is inherently hard. | Relevant | Accurate |
| 3 | What course sequence do students recommend for pre-med (gen chem, bio, ochem, biochem)? | Gated sequence; bio 2 before bio 1; gen chem → ochem → biochem. | Gen chem 1→2; take bio 2 before bio 1 (bio 1 needs gen chem 2); then ochem unlocks biochem; finish A&P early. | Relevant | Accurate |
| 4 | What do students think of Professor Schulze for HIST 1301? | Mixed — some warn bad reviews/avoid, others liked him. | Captures both sides: "great"/"not boring" vs "very very bad reviews" and "requires more effort than expected". | Relevant | Accurate |
| 5 | Is it manageable to take both 3000- and 4000-level IT courses together? | Cautionary on upper-level load (known coverage gap). | "I don't have enough information on that." | Off-target | Inaccurate (refused) |

**Result: 3/5 accurate, 2/5 refusals.** The system gives accurate answers when enough information is embedded, and refuses rather than hallucinate and make up answers.

**Retrieval quality (overall):** Mostly relevant — 3/5 queries retrieved on-topic chunks (Q2–Q4), one was only partially relevant (Q1), and one was off-target (Q5).

**Response accuracy (overall):** Accurate when grounded — every query with relevant retrieval (Q2–Q4) produced an accurate answer. The two failures (Q1, Q5) are over-refusals caused by weak retrieval, not hallucinations, which is the safer failure mode for this system.

---

## Failure Case Analysis

**Question that failed:** Q1 — "What do students say about taking multiple 2000-level CS courses in the same semester?"

**What the system returned:** "I don't have enough information on that." (no sources)

**Root cause:** Retrieval did return on-topic CS chunks at a moderate cosine distance (~0.45). But none of those comments specifically discuss "taking multiple 2000-level CS courses in the same semester". They discussed general first-year course load. Hence, they don't provide much context for the model to give an answer. The query is also very broad. Similarly, document 6 (IT workload) fails because the comments were about professors, but the query was about whether the workload is manageable or not.

**What you would change to fix it:** (1) **Content:** collect threads/comments that directly discuss CS and IT course-load combinations. (2) **Pipeline:** instead of a strict "no information available", maybe something related like "students don't address this exact combination, but generally say…" that helps them nonetheless. However, it risks the model making things up.

---

## Spec Reflection

**One way the spec helped you during implementation:** I'm a visual learner, so the **Architecture** section really helped me visualize the flow of data. The **Evaluation Plan** also helped me think about questions beforehand to correctly evaluate my model against the test cases.

**One way your implementation diverged from the spec, and why:** Initially I thought the posts and schedule should be embedded for the model to get the context and maybe provide personalized information for the user's query. Hence, I transcribed it into the document. I also noticed how the schedule was being included as a chunk, which is clearly bad chunking. Claude then recommended I narrow it down to only the comments from the OP and other students. This looks better and provides advice instead of including the user's problem. This is a trade-off.

---

## AI Usage

**Instance 1 — Cleaning data for chunking pipeline**

- *What I gave the AI:* Uploaded the schedule picture and the Reddit URL. Can u use this format and reddit link to fill it. Make sure the data for post and comments and replies is clean (without upvotes, date, emojis, and short useless comments like "lol") Include prof name, course number, name, day and date for scheule
MAJOR: Science (freshman)
SEMESTER: Spring 2024
SCHEDULE:
- CS 1336 Programming Fundamentals - Prof. Smith - MWF 10:00
- MATH 2413 Calculus I - TR 1:00
- CHEM 1311 General Chemistry - MWF 9:00
- RHET 1302 Rhetoric - online
Total: 13 credit hours

POST:
Rushing to lock in classes last-minute, is this doable? I'm worried about taking chem and calc in the same semester as a freshman.

COMMENTS:
- [commenter] Calc I and Chem together is fine for most people, but don't add a lab-heavy 4th course on top. Smith is a good intro prof.

- [commenter] Take RHET online like you have it, it frees up your week. Drop nothing — this is a light-ish load.

- [commenter] I did this exact schedule and the MWF 9am + 10am back-to-back was rough. Manageable but plan your mornings.  
- *What it produced:* Intially, it produced a very rough version like missing day and date for schedule and the non-indent replies. Sometimes Google gemini had problems reading the schedule image.
- *What I changed or overrode:* Followed up with prompts like "can u indent replies accordingly" and "add the date and time for the courses". Also turned to Claude to transcribe the uploaded schedule images.

**Instance 2 — Grounded generation**

- *What I gave the AI:* My retrieval approach section and the grounding requirement (answer from retrieved context only, with source attribution), and wire Groq generation onto the `retrieve()` function.
- *What it produced:* A working `ask()` with a grounding system prompt and a context block built from retrieved chunks.
- *What I changed or overrode:* I tightened the grounding to an exact refusal string and temperature 0, and insisted source attribution be programmatic (built from chunk metadata, deduplicated, with real Reddit URLs) rather than trusting the LLM to cite sources itself. I also added suppression of the source list on refusals, so a "don't know" answer doesn't display irrelevant citations.
