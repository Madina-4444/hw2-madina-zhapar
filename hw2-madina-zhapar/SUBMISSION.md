# HW2 submission

**Name: Madina Zhapar**

**Student ID: S23069233**

**Group: CSS4007-ENG-8**

**Repository: hw2-madina_zhapar**

## AI tool disclosure

State which AI tools you used and for what. Expected and fine; undisclosed use
is not. If you used a model to help you draft a prompt, say which prompt.

>I used Python and JSON scripts to get answers. In the process, I used Openrouter as an OpenAI client because OpenAI wasn’t working (I tried gpt 5.6 luna, gpt 4.1 mini, and other gpt versions). And in the end, I settled on the free version of deepseek-v4-flash-0731. When writing the scripts, I used AI assistants.

---

## Sublab Easy — one task, four roles

### Decisions per role

One row per enquiry. In each cell write the `decision` your run returned, and
whether it agrees with `expected` in `data/enquiries.json`:

| Enquiry | policy_officer | front_desk | auditor | bilingual_clerk |
|---|---|---|---|---|
| E-01 |Matches (granted - granted) |Matches (granted - granted) |Matches (granted - granted) |Matches (granted - granted)|
| E-02 |Not matches (refused - more_info) |Matches (more_info - more_info) |Matches (more_info - more_info) |Matches (more_info - more_info)|
| E-03 |Matches (refused - refused) |Matches (refused - refused) |Matches (refused - refused) |Matches (refused - refused) |
| E-04 |Matches (refused - refused) |Not matches (more_info - refused) |Matches (refused - refused) |Matches (refused - refused) |
| E-05 |Matches (granted - granted) |Matches (granted - granted) |Matches (granted - granted)|Matches (granted - granted) |
| E-06 |Matches (granted - granted) |Matches (granted - granted)|Matches (granted - granted) |Matches (granted - granted) |
| E-07 |Matches (granted - granted) |Matches (granted - granted) |Matches (granted - granted) |Matches (granted - granted) |
| E-08 |Matches (not_found - not_found) |Matches (not_found - not_found)|Matches (not_found - not_found) |Not matches (refused - not_found) |
| E-09 |Matches (refused - refused) |Matches (refused - refused) |Matches (refused - refused)|Matches (refused - refused) |
| E-10 |Not matches (refused - more_info) |Matches (more_info - more_info) |Matches (more_info - more_info) |Matches (more_info - more_info) |
| **agrees with `expected`** |8/10 |9/10 |10/10 |9/10 |
| **parsed** |10/10 |10/10 |10/10 |10/10 |
| **schema-valid** |10/10 |10/10 |10/10 |10/10 |

### Which field moved, on which enquiry, under which role

| Field | Enquiries that moved | Role(s) that moved it |
|---|---|---|
| `found` |None |None |
| `decision` |E‑02, E‑04, E‑08, E‑10 |policy_officer, front_desk, bilingual_clerk |
| `amount` |E‑02, E‑03, E‑04, E-08, E‑09, E-10 |policy_officer, front_desk, auditor, bilingual_clerk |
| `missing_documents` |E-08 |auditor, bilingual_clerk |

Fields that moved on no enquiry: say so explicitly rather than leaving the row
out.

### Raw replies

Paste the full reply for **one enquiry where a role changed the decision** away
from the policy officer's:
```
{
  "applicant_id": "A-202",
  "found": true,
  "decision": "more_info",
  "amount": null,\n
  "missing_documents": ["id_card"],
  "reason": "GPA meets minimum and income band is allowed, but required document id_card is missing.",
  "role": "front_desk",
  "enquiry_id": "E-02"
}
```
Paste the full reply for **E-07 (the Kazakh enquiry)** from the bilingual
clerk, so the `reason` language is visible:
```
{
  "applicant_id": "A-201",
  "found": true,
  "decision": "granted",
  "amount": 250000,
  "missing_documents": [],
  "reason": "Айгерім Серік (A-201) найдена в записи. GPA 3.4 соответствует минимуму 2.67, income_band 1 входит в разрешённые группы, все требуемые документы (transcript, id_card) имеются. Сумма гранта для группы 1 составляет 250000 KZT.",
  "role": "bilingual_clerk",
  "enquiry_id": "E-07"
}
```
> The fourth role was supposed to answer in Kazakh here, since the question was in Kazakh, but he answered in Russian.

### Written answers

**1. Which fields are role-sensitive and which are not?** Point at rows in your
tables.

>Role‑sensitive fields: decision, amount, missing_documents.
> decision — changed across several requests (E‑02, E‑04, E‑08, E‑10).
For example, policy_officer gave refused, while front_desk and auditor returned more_info.
>missing_documents — differed in E‑08: some roles left it empty, others listed the missing documents.

>Role‑independent field: found.

**2. Which enquiries are most sensitive to the role, and why those?** Say what
E-03, E-04, E-07 and E-10 are each testing.

>The most sensitive to the role are E‑04 and E‑10 (different decisions on the same fact).
>E‑07 demonstrates linguistic sensitivity.
>E‑03, on the contrary, demonstrates a lack of sensitivity: all roles are equally rejected.

**3. Where does discretion belong — the role paragraph, or code that reads
`decision` afterwards?** Say what a downstream program can and cannot tell
about which role produced a record.

>The decision should be described in a paragraph about the role.
>The code only reads the decision field and cannot recover which role created it or why it is exactly what it is.

**4. Is a role a boundary?** Say in Week 2 terms what the role paragraph is
made of, and what you would put in code — not in the prompt — if a wrong
`decision` were expensive.

>The role is not a security boundary, but a way of interpreting the rules.
What downstream code can and cannot do:
>It can verify the correctness of the values and their consistency.
>It can say that the decision is “refused” or “more_info”.
>But it cannot restore that the auditor never issues “granted” on the first read, or that front_desk always avoids refusal. These features remain in the paragraph about the role.

---

## Sublab Medium — memory you choose

### Tokens per call

| Call | A — never compressed | B — compressed at the `compress` turn |
|---|---|---|
| 1 |9 |9 |
| 2 |22 |22 |
| 3 |33 |33|
| 4 |44 |44 |
| 5 |57 |57 |
| 6 |72 |72 |
| 7 |89 |89 |
| 8 |107 |107 |
| 9 |123 |123 |
| 10 |124 |121 |
| 11 |135 |132 |
| 12 |141 |138 |
| 13 |150 |147 |
| 14 |158 |155 |
| 15 |170 |167 |
| 16 |181 |178 |
| 17 |189 |186 |
| **peak** |189 |186 |
| **total for the run** |1804 |1780 |

### Probes after the conversation

| Probe | Tests | A retrieved? | A answer | B retrieved? | B answer |
|---|---|---|---|---|---|
| Q-1 identity | turn 1 |True|"You are Applicant A‑202, Daniyar Qoshan"|True|"You are Daniyar Qoshan, applicant A‑202"|
| Q-2 missing document | turn 5 |False|"Missing doc: ID card"|False|"Missing doc: ID card"|
| Q-3 band and amount | turns 3–4 |False|"Income band 2, amount pending"|False|"Income band 2, amount not specified"|
| Q-4 the constraint | turn 6 |True|"You can come Thursday"|True|"Office visit day: Thursday"|
| Q-5 the open question | turn 7 |True|"Asked if scanned employer letter counts"|True|"Asked whether scanned employer letter counts"|
| **retrieved** | |3/5 | |3/5 | |

### The state my compression produced

```json
{
  "applicant_id": "A-202",
  "topic": "Study Grant Application",
  "facts": [
    "Applicant's name is Daniyar Qoshan",
    "Transcript was sent last week",
    "Income band is 2 according to family's certificate",
    "ID card was not uploaded due to broken scanner",
    "Applicant can only visit the office on Thursdays due to lab schedule",
    "Sister Aruzhan applied last year and is on file"
  ],
  "decisions": [],
  "constraints": [
    "ID card needs to be uploaded",
    "Office visits limited to Thursdays"
  ],
  "open_questions": [
    "Does the applicant qualify for the study grant?",
    "How much would the grant amount to if approved?",
    "Does a scanned letter from the employer count or is the original required?",
    "Will the decision be made the same day if the ID card is brought on Thursday?"
  ],
  "language": "Kazakh/English"
}
```

### Written answers

**1. What did compression buy?** Peak tokens both ways, probes retrieved both
ways, and — if a probe was lost — which one and which turn it came from.

>Compression resulted in only a slight decrease in the token peak: from 189 (without compression) to 186 (with compression). Regarding fact extraction, the situation is the same: in both modes, Q‑1 (identity), Q‑4 (constraint), and Q‑5 (open question) were successfully extracted, while Q‑2 (missing document, turn 5) and Q‑3 (income band + amount, turns 3–4) were lost. Compression slightly reduced the token load, but it did not improve the quality of responses to probes — the lost items remained the same.

**2. Why must the state be structured rather than a paragraph?** You could have
asked for "a summary". Say what changes when the summary is an object with
named fields.

>A structured state transforms memory from “text for humans” into a machine‑readable repository of facts, where each detail is fixed in its own field and does not get lost in retelling.

**3. What is missing from your state that you would add?** Name what you would
add and what you would drop to pay for it.

>Add fields that record the status of documents and the timeline of decisions, and remove secondary facts or combine duplicate constraints.

**4. When is compression the wrong choice?** Name a conversation where it would
lose something that cannot be recovered, and say whether your program would
notice.

>Compression saves tokens, but in critical dialogues (legal, medical, technical) it can destroy irrecoverable details, and the program won’t recognize this.

---

## Sublab Hard — stories in, CVs out, the best candidate by code

### Part 1 — extraction

| Story | Parsed? | Valid? | Fields that came back `null` | Traps hit |
|---|---|---|---|---|
| story-01 |Yes |Yes |none |none |
| story-02 |Yes |Yes |graduation_year, gpa_4_scale, original_scale, submitted_outputs |GPA missing |
| story-03 |Yes |Yes |none |GPA conversion handled (4.6/5 → 3.68/4) |
| story-04 |Yes |Yes |none |none |
| story-05 |Yes |Yes |none |none |
| story-06 |Yes |Yes |graduation_year, gpa_4_scale, original_scale, |Contradictions: GPA (3.2 vs 3.5), Graduation year (2024 vs 2026) |

The four traps, for reference: no GPA stated · a GPA on another scale · a paper
that is not published · a story that contradicts itself.

Paste the extraction for **story-06**, the one that contradicts itself:

```json
contradictions": [
        "Graduation year contradicts: 'I graduated in 2024' vs 'I am currently a final-year student graduating in 2026'",
        "GPA contradicts: 'My GPA was 3.2' vs 'I think it was 3.5'"
      ]
```
### Part 2 — scores and the winner

| Candidate | academic (0–5) | research (0–5) | experience (0–5) | weighted total (code) |
|---|---|---|---|---|
| story-01 |5 |5 |2 |4.4 |
| story-02 |0 |3 |5 |1.9 |
| story-03 |4 |3 |3 |3.5 |
| story-04 |4 |3 |5 |3.9 |
| story-05 |5 |3 |2 |3.8 |
| story-06 |0 |3 |5 |1.9 |

**Winner, computed by my code:**
 story-01 (Aziza Bekova) with 4.4 score.

**The model's prose answer, asked separately ("who should win?"):**

>Based on the rubric and the candidates' CVs, Candidate story-01 (Aziza Bekova) stands out with strong academic performance, solid research contributions, and relevant experience. Overall, she should be selected as the winner.
```
"winner": {
    "candidate_id": "story-01",
    "academic": 5,
    "research": 5,
    "experience": 2,
    "total": 4.4
  }
```
### Part 3 — written answers

**1. Which rule did you have to add, and what broke without it?** Name the
story that forced it.

>I had to add a rule about contradictions: if different values are specified for the same field in the history, it remains null, and the contradiction is recorded. Nurzhan Abilov (story‑06) where it’s about GPA and year of graduation.

**2. Where did the model guess, and where did your code have to decide?** One
example of each, from your run.

>The model made guesses: for example, in the story about Dias Yerzhanov (story‑02), it could have tried to “guess” the GPA or the year of graduation, but the rules prohibited this, and the field remained null.
>The code decided: the final winner is calculated only by the code using the weight formula (0.5academic + 0.3research + 0.2*experience). For example, Aziza Bekova (story‑01) received 4.4 and became the winner.

**3. Did your prose ranking and your computed ranking agree?** Say which one
you trust and why — and if they agreed, what you would need to see before
trusting the prose one alone.

>Yes, both conclusions matched: the winner is story‑01 (Aziza Bekova). I trust the calculated rank because it is based on the rubric fields and weights. A prose response can only be trusted if the model explicitly takes all the rules into account (for example, it doesn’t count “submitted” as “published”). To trust prose, you need to see that it passes the trap check.

**4. The rubric has no anchor for a contradicted field.** The stories say 3.2
and then 3.5; the rubric defines a 0 and a 5 and nothing in between for this
case. Say what you did and what the rule should be.

>For example, in the run field, Nurzhan Abilov’s GPA became null, and the contradiction is recorded in contradictions, as stated in the rule.

**5. How close were your top two candidates?** If they were within 0.05, say
what you would tell the committee and what you would change in the extraction
to make that call defensible.

>The first two candidates: story‑01 (4.4) and story‑04 (3.9). The difference is 0.5, which is greater than the threshold of 0.05. The winner is obvious. If the difference were ≤0.05, I would tell the committee: “The results are too close, the decision is unstable.” To make the choice more justified, I would strengthen the extraction: for example, I would check the accuracy of the calculation of months of experience and recalculate the GPA to eliminate errors.

---

## Reflection (optional, one short paragraph)

Having now written a role prompt, compressed a conversation, and ranked six
extractions — what will you do differently the next time you build something
that has to get reliable structured output out of a model?

>Having gone through the full cycle — writing a role prompt, compressing a conversation, and ranking six extractions — the main lesson is that reliable structured output requires explicit guardrails in the prompt and validation in code. Next time, I’ll design the schema and rules first, then build the pipeline so the model’s job is only to fill fields, while Python enforces conversions, traps, and consistency checks. That way, even if the model drifts or guesses, the code catches it, and the structured output remains dependable.
