# Project 1 Planning: The Unofficial Guide

> Write this document before you write any pipeline code.
> Your spec and architecture diagram are what you'll use to direct AI tools (Claude, Copilot, etc.) to generate your implementation — the more specific they are, the more useful the generated code will be.
> Update the Retrieval Approach and Chunking Strategy sections if you change your approach during implementation.
> Update this file before starting any stretch features.

---

## Domain

<!-- What domain did you choose? Why is this knowledge valuable and hard to find through official channels? -->
My domain is Academics that includes courses, professors, exams and grading for CS at UMD. UMD students often find it difficult to find information related to academics in one place. And usually, official channels like the university website or course catalog may not provide detailed insights into professors' teaching styles, course difficulty, or grading patterns. This system makes that informal knowledge searchable and accessible, helping students make informed decisions about their academic choices.
---

## Documents

<!-- List your specific sources: URLs, subreddit names, forum threads, or file descriptions.
     Aim for at least 10 sources that together cover different subtopics or perspectives within your domain. -->

| # | Source | Description | URL or location |
|---|--------|-------------|-----------------|
| 1 | Planet terp Professors | Student reviews of UMD professors       | https://planetterp.com/professors        |
| 2 | Planet terp CS courses | Student reviews of CS Courses at UMD    | https://planetterp.com/search?query=CMSC |
| 3 | Planet terp Grades     | Grades categorized by courses/Professors| https://planetterp.com/grades            |
| 4 | Rate my professor      |Student reviews of professors in RMP     | https://www.ratemyprofessors.com/school/1270 |
| 5 | r/UMD - CS Opportunities | Students discussion threads for Job/Intern opp.| https://www.reddit.com/r/UMD/search/?q=CS+opportunities |
| 6 | r/UMD - thread of Professors| Student discussion on Professors | https://www.reddit.com/r/umd/search/?q=professor|
| 7 | r/UMD - CMSC| Student threads on CMSC courses | https://www.reddit.com/search/?q=UMD+CMSC |
| 8 | r/UMD - exams|Students advice/discussion on exams |https://www.reddit.com/search/?q=UMD+exam+advice |
| 9 | r/UMD - CS grades| Students advice/offer comfort on bad grades  |https://www.reddit.com/r/UMD/search/?q=grade+CS |
| 10 | UMD official reddit | Advice for freshman related to acads |https://www.reddit.com/r/UMD/wiki/marylandprotips/?screen_view_count=6 |

---

## Chunking Strategy

<!-- How will you split documents into chunks?
     State your chunk size (in tokens or characters), overlap size, and explain why those
     numbers fit the structure of your documents.
     A review-heavy corpus warrants different chunking than a long FAQ. -->

**Chunk size:** Use source-aware chunks: 300-400 tokens for review and discussion text(keep whole text if short review(<= 50-65 tokens)), section-sized chunks for structured pages, and row-sized chunks for grade or record data.

**Overlap:** 50 tokens for narrative text; none for table-like or atomic records.

**Reasoning:** The corpus mixes long informal threads with more structured factual pages, so one fixed chunk rule would either add too much noise or cut answers apart. Smaller overlapping chunks help preserve context in reviews and Reddit posts, while structured pages are better kept at natural boundaries so retrieval returns a complete fact instead of a split fragment.

---

## Retrieval Approach

<!-- Which embedding model are you using (e.g., all-MiniLM-L6-v2 via sentence-transformers)?
     How many chunks will you retrieve per query (top-k)?
     If you were deploying this for real users and cost wasn't a constraint, what tradeoffs
     would you weigh in choosing a different embedding model — context length, multilingual
     support, accuracy on domain-specific text, latency? -->

**Embedding model:** 
all-MiniLM-L6-v2 via sentence-transformers for general semantic understanding, supplemented by a domain-specific fine-tuned model if available to better capture nuances in academic reviews and discussions.

**Top-k:**
For tokens around 300-400, I would retrieve top 5 chunks as starting point to balance relevance and context. For even shorter chunks, I would go with top 3. Because higher chunks would lead to more noise and extremely lower chunks would make LLM hallucinate.

**Production tradeoff reflection:**
I would choose an embedding model that offers longer context windows to better understand full length of reviews and thread discussions even at the cost of higher latency. I would also add multilingual support which would cater to wider student body. As for domain-specific accuracy, I would consider fine-tuning a model that was trained on academic reviews and discussions, so that it can understand the semantic nuances of student feedback and advice. 
---

## Evaluation Plan

<!-- List your 5 test questions with their expected correct answers.
     Questions should be specific enough that you can judge whether the system's response
     is right or wrong. "What are good dining halls?" is too vague.
     "What do students say about wait times at [dining hall name] during lunch?" is testable. -->

| # | Question | Expected answer |
|---|----------|-----------------|
| 1 | | |
| 2 | | |
| 3 | | |
| 4 | | |
| 5 | | |

---

## Anticipated Challenges

<!-- What could go wrong? Name at least two specific risks with reasoning.
     Consider: noisy or inconsistent documents, missing source attribution, off-topic
     retrieval, chunks that split key information across boundaries. -->

1.

2.

---

## Architecture

<!-- Draw a diagram of your pipeline showing the five stages:
     Document Ingestion → Chunking → Embedding + Vector Store → Retrieval → Generation
     Label each stage with the tool or library you're using.
     You can use ASCII art, a Mermaid diagram, or embed a sketch as an image.
     You'll use this diagram as context when prompting AI tools to implement each stage. -->

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
