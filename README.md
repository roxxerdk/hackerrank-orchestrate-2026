# WhatsApp Multimodal Notification Router

An advanced, production-grade personalized notification router designed to filter the noise of modern messaging. 

While typical systems rely on simple keyword matches or generic LLM calls that are slow and expensive, this router runs a hybrid pipeline: a deterministic rule retrieval parser paired with personal interaction history context to classify and route notifications in **under 8 milliseconds**.

---

## What Makes This Router Different?

Most notification filters treat all users or messages the same. This system solves personalization, safety, and scale differently:

### 1. Zero-LLM Fast Execution (Sub-8ms Latency)
Typical LLM agent pings take 1 to 3 seconds, which is too slow for real-time notification routing. This system loads context datasets into memory, compiles features, and evaluates decisions in **~7.7 ms** (Feature Extraction: ~7.4ms, Reasoning Engine: ~0.3ms).

### 2. Personalized Context Mappings
Instead of matching rules globally, the features extraction context queries user-specific indices:
*   **Recipient Preferences**: Recipient opens, replies, dismissals, and quiet DND hours.
*   **Relationship History**: User-sender messaging activity history, reply counts, and domain matching validations.
*   **Group Dynamics**: Mute state, role admin flags, and target group member counts.

### 3. Decoupled Rule Retrieval & Priority Conflict Engine
Rules are stored in a modular repository. A retrieval engine pulls rules dynamically based on context features and passes them to a reasoning engine. Conflicts are resolved using priority bands (Safety > User Preference > Business > Urgency > Relationship > System Alert) and deterministic tie-breakers.

### 4. Media Cache Resolution
To verify image QR codes, deadlines, or voice note payment requests without blocking execution threads, the extractor dynamically resolves file sizes and uses an asynchronous analysis loader cache.

### 5. Automated Regression & Error Analysis Dashboard
Includes a built-in evaluation framework:
*   **Precision Dashboards**: Flags weak rules (precision <50%) or rules with low evidence counts.
*   **Error Analytics**: Automatically groups misclassifications by expected-predicted transitions (e.g. NOTIFY -> DIGEST) to find rule deficiencies.
*   **Regression Guardrails**: Keeps historical best benchmarks and fails pipeline builds if changes regress accuracy.

---

## System Architecture

```text
       [ WhatsApp Incoming Notification ]
                     │
                     ▼
          [ Feature Extraction ]
      ├── Text parsing (links, urgency flags)
      ├── Media Cache (QR, payment signals)
      └── Personalized Index Context (DND, history)
                     │
                     ▼
             [ Context Builder ]
      Maps raw metrics to ReasoningContext schema
                     │
                     ▼
             [ Rule Retrieval ]
      Selects rules triggered by active signals
                     │
                     ▼
          [ Reasoning & Tie-Breaker ]
      Resolves rule conflicts by priority bands
                     │
                     ▼
         [ Confidence Calibration ]
      Applies bonuses & safety penalties
                     │
                     ▼
         [ Output Submission Generator ]
      Computes message types, reasons, & evidence
```

---

## Folder Layout

```text
code/
├── app/
│   ├── api/                 # FastAPI routes, dependencies, and exception handlers
│   ├── evaluation/          # F1 metrics, error analysis, rule dashboards, threshold optimizers
│   ├── features/            # Context builders, extractors, and features contracts
│   ├── media/               # Media signals loaders and analysis cache loaders
│   ├── output/              # Final submission prediction formatting
│   ├── persistence/         # Atomic JSON result store backend
│   └── reasoning/           # Decision engine, confidence scorer, rule repository
├── tests/                   # Verification suite (39 unit tests)
├── demo_e2e.py              # End-to-end single message routing demo run
├── run_submission.py        # Generates final output.csv predictions
└── requirements.txt         # Package footprints specifications
```

---

## Setup & Running

### 1. Installation
Install the project dependencies:
```bash
pip install -r requirements.txt
```

### 2. Run the End-to-End Demo
Process a single sample message payload to see the pipeline:
```bash
python code/demo_e2e.py
```

### 3. Generate Submission Predictions (`output.csv`)
Compile predicted actions, types, reasons, and evidence IDs for all messages:
```bash
python code/run_submission.py
```

### 4. Start the FastAPI Gateway
Launch the local web server:
```bash
uvicorn app.api.app:app --reload --port 8000
```
Interactive documentation is available at `http://localhost:8000/docs`.

### 5. Run Evaluations & Rules Precision Dashboard
Calculate performance metrics and run error analyses against ground truth datasets:
```bash
python -m app.evaluation.evaluator
```

### 6. Run the Test Suite
Run the 39 unit tests:
```bash
pytest code/tests/
```

---

## Production API Endpoints

*   `GET /health/live`: Web liveness checkpoint.
*   `GET /health/ready`: readiness status (verifies context indices are loaded in memory).
*   `GET /metrics`: Incremental processed logs, latencies, and rule trigger counts.
*   `GET /version`: Pipeline, features schema, and ruleset version indicators.
*   `POST /route`: Evaluates a single message structure.
*   `POST /route/batch`: Evaluates a collection of messages.

---

## Performance Statistics

*   **Average Latency**: `~7.7 ms`
    *   *Feature Context Extraction*: `~7.4 ms`
    *   *Reasoning and Decision Engine*: `~0.3 ms`
*   **Test Suite Status**: `39 Passed / 0 Failed`
