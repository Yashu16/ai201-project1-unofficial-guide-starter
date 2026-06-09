# The Unofficial Guide — Project 1

> **How to use this template:**
> Complete each section *after* you've built and tested the corresponding part of your system.
> Do not write placeholder text — if a section isn't done yet, leave it blank and come back.
> Every section below is required for submission. One-liners will not receive full credit.

---

## Domain

<!-- What topic or category of knowledge does your system cover?
     Why is this knowledge valuable, and why is it hard to find through official channels?
     Example: "Student reviews of CS professors at [university] — useful because official
     course descriptions don't reflect teaching style, exam difficulty, or workload." -->
My domain is Academics that includes courses, professors, exams and grading for CS at UMD. UMD students often find it difficult to find information related to academics in one place. And usually, official channels like the university website or course catalog may not provide detailed insights into professors' teaching styles, course difficulty, or grading patterns. This system makes that informal knowledge searchable and accessible, helping students make informed decisions about their academic choices.
---

## Document Sources

<!-- List every source you collected documents from.
     Be specific: include URLs, subreddit names, forum thread titles, or file names.
     Aim for variety — sources that together cover different subtopics or perspectives. -->

| # | Source | Type | URL or file path |
|---|--------|------|-----------------|
| 1 | Planet terp CMSC Reviews | Student reviews of UMD CS professors       | "https://planetterp.com/api/v1/courses?department=CMSC&reviews=true&limit=100"|
| 2 | Planet terp CMSC Reviews | Student reviews of UMD CS profs but different courses |"https://planetterp.com/api/v1/courses?department=CMSC&reviews=true&limit=100&offset=100"|
| 3 | UMD CS current students   | Resources relating to current students | "https://undergrad.cs.umd.edu/current"|
| 4 | Rate my professor      |Student reviews of professors in RMP     | https://www.ratemyprofessors.com/school/1270 |
| 5 | r/UMD - CS Opportunities | Students discussion threads for Job/Intern opp.| "https://www.reddit.com/r/UMD/search/?q=CMSC+internship+research+opportunity&restrict_sr=1" |
| 6 | r/UMD - thread of Professors| Student discussion on Professors | "https://www.reddit.com/r/UMD/search/?q=professor+review+class+CMSC&restrict_sr=1"|
| 7 | r/UMD - CMSC| Student threads on CMSC courses | "https://www.reddit.com/r/UMD/search/?q=CMSC+course+review&restrict_sr=1" |
| 8 | r/UMD - exams|Students advice/discussion on exams |"https://www.reddit.com/r/UMD/search/?q=CMSC+exam+midterm+final&restrict_sr=1"|
| 9 | r/UMD - CS grades| Students advice/offer comfort on bad grades  |"https://www.reddit.com/r/UMD/search/?q=CMSC+grade+GPA&restrict_sr=1" |
| 10 | UMD official reddit | Advice for freshman related to acads |https://www.reddit.com/r/UMD/wiki/marylandprotips/?screen_view_count=6 |
| 11 | UMD FAQ | Official FAQ for UMD students |  "https://undergrad.cs.umd.edu/faq" |

Updating above links because previous ones were not working, I was wrong about certain links. I have also added two official UMD sources so that students can find almost everything just by asking LLM instead of having to go through multiple sources.
---

## Chunking Strategy

<!-- Describe your chunking approach with enough specificity that someone else could reproduce it.
     Include:
     - Chunk size (characters or tokens) and why that size fits your documents
     - Overlap size and why (or why not) you used overlap
     - Any preprocessing you did before chunking (e.g., stripping HTML, removing headers)
     - What your final chunk count was across all documents -->

**Chunk size:** Use source-aware chunks: 300-400 tokens for review and discussion text(keep whole text if short review(<= 50-65 tokens)), section-sized chunks for structured pages, and row-sized chunks for grade or record data.

**Overlap:** 50 tokens for narrative text; none for table-like or atomic records.

**Why these choices fit your documents:** The corpus mixes long informal threads with more structured factual pages, so one fixed chunk rule would either add too much noise or cut answers apart. Smaller overlapping chunks help preserve context in reviews and Reddit posts, while structured pages are better kept at natural boundaries so retrieval returns a complete fact instead of a split fragment.

**Final chunk count:** 4938 (I know the project instruction said above 2000 would lead to bad retrieval, however, I found based on number of reviews and the way I chunked each review mostly as is, I got way higher than expected while also working almost perfectly.)

---

## Embedding Model

<!-- Name the embedding model you used and explain your choice.
     Then answer: if you were deploying this system for real users and cost wasn't a constraint,
     what tradeoffs would you weigh in choosing a different model?
     Consider: context length limits, multilingual support, accuracy on domain-specific text,
     latency, and local vs. API-hosted. -->

**Model used:** all-MiniLM-L6-v2 via sentence-transformers for general semantic understanding and faster inference. Also used for its small size and fast processing time.

**Production tradeoff reflection:**
I would choose an embedding model that offers longer context windows to better understand full length of reviews and thread discussions even at the cost of higher latency. I would also add multilingual support which would cater to wider student body. As for domain-specific accuracy, I would consider fine-tuning a model that was trained on academic reviews and discussions, so that it can understand the semantic nuances of student feedback and advice. I would also consider hosting the model locally to reduce latency and ensure data privacy, especially since student reviews may contain sensitive information. However, I would need to weigh this against the maintenance and infrastructure costs of running a local model versus using an API-hosted solution that abstracts away those concerns.
---

## Grounded Generation

<!-- Explain how your system enforces grounding — how does it prevent the LLM from answering
     beyond the retrieved documents?
     Describe both your system prompt (what instruction you gave the model) and any structural
     choices (e.g., how you formatted the context, whether you filtered low-relevance chunks).
     Do not just say "I told it to use the documents" — show the actual instruction or explain
     the mechanism. -->

**System prompt grounding instruction:** """You are a helpful academic advisor for UMD (University of Maryland) CS students.
You answer questions EXCLUSIVELY using the retrieved source chunks provided in the user message.
You must NOT use any knowledge from your training data.

Rules:
- If the provided chunks contain enough information to answer the question, answer it clearly and concisely.
- If the chunks do not contain sufficient information, respond with exactly:
  "I don't have enough information in the retrieved sources to answer this question."
- Never fabricate, infer beyond what is stated, or supplement with outside knowledge.
- Attribute your answer to the sources (e.g., "According to PlanetTerp reviews..." or "Reddit students mention...").
- Keep answers focused and grounded in the exact text of the chunks."""



**How source attribution is surfaced in the response:**
Source attribution is enforced by instructing the model to explicitly mention the source of information in its response. It is shown above in the rules section of system prompt.

**Structural choices**
I have wrapped chunks in delimiters as "Retrieved sources" and "End of sources" with chunks getting numbered labels [1], [2], etc. 

Also, chunks above Retrieval_score_cutoff are dropped before reaching the LLM, so low-relevance chunks are filtered out in retrieval stage. 

If there were no chunks retrieved, LLM never gets called and the default message is "I don't have enough information in the retrieved sources to answer this question." This way it wouldn't hallucinate. 
---

## Evaluation Report

<!-- Run your 5 test questions from planning.md through your system and record the results.
     Be honest — a partially accurate or inaccurate result that you explain well is more
     valuable than a suspiciously perfect result. -->

| # | Question | Expected answer | System response (summarized) | Retrieval quality | Response accuracy |
|---|----------|-----------------|------------------------------|-------------------|-------------------|
| 1 | Which CMSC professor is known for giving the most useful feedback on assignments?| Accoding to PlanetTerp/Reddit: Professor X is well known for giving you not only their grades but also most useful feedback, infact, that feedback will help you in your midterms/finals.| According to PlanetTerp reviews, Professor Michael Hicks is known for being understanding and willing to adjust coursework/scores to help students succeed when they reach out to him, implying that he provides useful feedback on assignments.| Partially relevant| Partially Accurate |
| 2 | Is CMSC351 actually as hard as people say, and how bad is the grade distribution? |According to this Planet Terp grade distribution and planet terp CMSC351 course reviews: It depends on the professor you get, but it generally is difficult. Most students tend to get average grades in this course. |According to PlanetTerp CMSC Reviews, CMSC351 is not as hard as people say. One review mentions that "the class is heavily curved" and "the pass/fail rate for Kruskal's 351 is also comparable to any other CS classes," suggesting that the grade distribution is not overly harsh. Another review states that "if you studied the course content thoroughly, you would likely come across some of the stuff we were tested on," implying that the exams are manageable with proper preparation. |Relevant | Accurate |
| 3 |What do students wish they knew before taking CMSC216? |According to Planet Terp and Reddit posts: You need to be well-versed with basic programming, and plan ahead for your projects and tests. Be good in C as this course is taught in that language. |According to PlanetTerp CMSC Reviews, students wish they knew that Professor Yoon's lecture style can be difficult to keep up with, and that his exams are tricky with many "catch" questions. They also wish they knew that Professor Kauffman's projects are pretty tough, but that there is ample opportunity to ace them if started early. Furthermore, some students wish they knew about Professor Kauffman's teaching style and language barriers before taking the class, as it caused significant difficulties for them. | Relevant| Accurate|
| 4 | How do TAs and office hours actually work in upper-level CS courses at UMD?| According to these reddit posts: It's usually drop-in office hours instead of appointemnet based, and TAs will guide you with your project but mostly it needs to be done by you| According to PlanetTerp CMSC Reviews, in upper-level CS courses at UMD, the effectiveness of TAs and office hours can vary. In some cases, such as with Professor Nelson Padua-Perez in CMSC131, TA office hours are reported to run smoothly, from 9-5 weekdays, making it easy to get help. However, in other cases, like with Professor Gonzales in CMSC132, office hours are described as "brutal and a complete mess" with TAs often canceling or rescheduling, leaving students without adequate support. Additionally, some students mention that they stopped attending office hours due to the difficulties in getting help, and instead opted to work on their own or seek alternative resources.| Relevant|Accurate |
| 5 |Is the CS internship/research scene at UMD competitive, and how do students break in? |According to Official UMD reddit: Go to your professor early if you want to work on research, understand their work and see if it aligns with your interests. As for internships, you tend to get government projects because of how UMD is located near DC  |According to r/UMD CS Opportunities, the CS internship and research scene at UMD is somewhat competitive, with students noting that internships are "hard to get" and require applying to "hundreds of places every cycle." However, students also mention that UMD has a lot of opportunities to connect with companies and strengthen resumes through school opportunities. To break in, students advise talking with professors, showing initiative, and demonstrating interest in research areas, such as cybersecurity or robotics. Some professors may give students a practice problem to screen out those who are not serious, and students who can "knock it out of the park" may be given opportunities. Additionally, students suggest starting to work on personal projects early and staying active in the community to network and increase chances of landing internships. |Relevant |Partially Accurate |

**Retrieval quality:** Relevant / Partially relevant / Off-target  
**Response accuracy:** Accurate / Partially accurate / Inaccurate

---

## Failure Case Analysis

<!-- Identify at least one question where retrieval or generation did not work as expected.
     Write a specific explanation of *why* it failed, tied to a part of the pipeline.

     "The answer was wrong" is not an explanation.

     "The relevant information was split across a chunk boundary, so retrieval returned
     only half the context — the model didn't have enough to answer correctly" is an explanation.

     "The embedding model treated the professor's nickname as out-of-vocabulary and returned
     results from an unrelated review" is an explanation. -->

**Question that failed:** 
what information do you have for CMSC132
**What the system returned:** 
According to PlanetTerp CMSC reviews, CMSC132 has been taught by multiple professors, including Shyam Pujara, Pedram Sadeghian, and Hrishik Rajendra, with varying ratings:

Shyam Pujara received a 5/5 rating with an expected grade of A+,
Pedram Sadeghian received a 4/5 rating with an expected grade of C+,
Hrishik Rajendra received a 5/5 rating with an expected grade of A+.
Students praise Shyam Pujara and Hrishik Rajendra as excellent TAs, while Pedram Sadeghian's review notes that he does his job in making CMSC131 and CMSC132 "weed out classes".

**Root cause (tied to a specific pipeline stage):**
This would be a Noisy Chunk problem, here LLM says three people are professors of CMSC132 but later contradicts it saying two of them are TAs. Probably the chunk it first retrieved didn't mention their roles and LLM assumed them to be professors but later chunks filled in the role, and it clarifies. 

**What you would change to fix it:**
I would strengthen the system prompt saying not to fill in a person's role unless explicitly stated in the retrieved chunks.
---

## Spec Reflection

<!-- Reflect on how planning.md shaped your implementation.
     Answer both questions with at least 2–3 sentences each. -->

**One way the spec helped you during implementation:**
I was able to understand the entire process before proceeding further, which helped me understand that ingestion and chunk generation are critical steps, and if they are not done properly, the rest of the pipeline will be affected.

Also, I have learned that the proper way to implement a project with help of AIs would be to first write down my decisions in a planning document, and ask AI to generate the code based on that. Then I would experiment, and change things based on the results.
**One way your implementation diverged from the spec, and why:**
Well, my initial source links were extremely bad, it was not the way I expected it to work, the ingestion part did not work. So, I had to change my source links and improve the way I was fetching the data.

And I said I would use copilot for milestone 4 and 5, but it hit some limtations and I had to change to Claude. 
---

## AI Usage

<!-- Describe at least 2 specific instances where you used an AI tool during this project.
     For each: what did you give the AI as input, what did it produce, and what did you
     change, override, or direct differently?

     "I used Claude to help me code" is not sufficient.
     "I gave Claude my Chunking Strategy section from planning.md and asked it to implement
     chunk_text(). It returned a function using a fixed character split. I overrode the
     chunk size from 500 to 200 because my documents are short reviews, not long guides." -->

**Instance 1**

- *What I gave the AI:* I asked Claude to generate ingestion and generator code based on my planning document, with the links I gave. 
- *What it produced:* The chunks it generated were improper with some going off-topic in reddit threads(like bringing everything that has to do with professor and it even included other colleges when it was supposed to be UMD) along with some sources not working at all.
- *What I changed or overrode:* I changed the code to check for r/UMD only for reddit threads, and updated planet terp links based on the API documentation, while also adding two official UMD sources to make it to 10+ sources while also giving more variety.

**Instance 2**

- *What I gave the AI:* I asked Claude to implement the retrieval function based on my planning document. The inital distance was set to 0.8 in config based on instructions from project. 
- *What it produced:* It was returning chunks that were not relevant to the question, and it was also not returning many chunks.
- *What I changed or overrode:* So I have increased the distance to 1.2 and I have seen more relevant chunks to be added, and even top 3 chunks are relevant to the question.  
