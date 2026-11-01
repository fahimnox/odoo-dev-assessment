# Stage 00 — Read the assessment and establish the working contract

- **Date:** 2026-11-01
- **Tool / model:** Claude Code, Opus 5.5 (`claude-opus-5-5`)
- **Working directory:** the assessment kit root (`<kit-root>`)
- **Commits:** `50c1465` (Stage 00 files), followed by the commit adding this log

**Transcription method:** see [README.md](README.md). User text, the referenced instruction file, and the assistant's visible messages are verbatim. Tool activity is a labeled summary.

## User prompt (verbatim)

```text
Read prompts/00_operating_contract.txt and execute Stage 00 only.
```

## Referenced instruction file: `prompts/00_operating_contract.txt` (verbatim)

```text
STAGE 00 — Read the assessment and establish the working contract

You are my hands-on Odoo development partner and tutor. I am Mohamed, an experienced Python/Django developer who is new to Odoo. The assessment explicitly permits/recommends GenAI, and my team lead has encouraged this workflow. Help me implement, test, understand, and honestly present the work. I will use you through a terminal with permission to create files, install required development dependencies, run services, and execute tests in this local project.

LOCATION AND SCOPE
- The current directory is the extracted assessment kit. Read reference/assessment.pdf first. If that exact file is absent, locate the supplied assessment within this directory; ask for its path only if you cannot find it. Do not search unrelated personal directories.
- Read PROMPT_SHEET_EN.md for the stage map. Execute only the stage I explicitly request; do not run the entire sheet automatically.
- Our selected exercises are Exercise 1, azk_odoo_partner_monitor, and Exercise 2, Dynamic Trial Balance. Exercise 3/POS is out of scope unless I explicitly change this decision.
- Use Odoo 18 Community as a documented working assumption, not an employer-confirmed requirement. Check any clarification I provide before proceeding. Implement both exercises fully within this edition; do not silently depend on Enterprise-only modules or reduce mandatory features to fit the edition.
- Create the implementation repository under solution/. Keep the reference PDF, this kit, private study notes, and local runtime outside the published repository. Keep Odoo core in a separate runtime checkout or image; do not vendor or modify it.

PERSISTENT CONTRACT
Unless explicitly stated otherwise, docs/* paths refer to solution/docs/*. Create or carefully merge solution/AGENTS.md with these rules. Preserve existing unrelated work and instructions. Inspect Git status before edits; use a dedicated local branch where appropriate.
1. Read the actual pinned Odoo 18 source and official documentation before choosing version-sensitive models, fields, XML syntax, report APIs, frontend imports, or cron APIs. Do not invent names or copy APIs from other versions.
2. Implement the simplest complete solution. No core patches, dummy success responses, fake dashboards, TODO stubs presented as complete, or extra infrastructure without a concrete need.
3. Routine reversible project setup and dependency installation are authorized. Inspect OS, shell, resources, and existing tooling first. Use isolated dependencies and dedicated assessment databases. Never overwrite unrelated services/data. If host privileges, a reboot, credentials, or a genuine environment limitation require my action, explain the one necessary step and continue independent work.
4. Test what you claim. Distinguish PASS, FAIL, BLOCKED, and NOT RUN. Never invent tests, screenshots, live-site observations, package versions, or terminal output. Do not mark a test skipped as passed.
5. Keep a requirement-to-implementation-to-test matrix. Record ambiguities, defaults, implementation deviations, and limitations explicitly. The PDF remains the source of requirements; your interpretations are assumptions until confirmed.
6. Log the actual visible prompt and response for every stage under docs/ai/. Preserve exact visible text where available; export the CLI's visible transcript if supported. Label summaries as summaries. Do not fabricate missing history or claim the prompt sheet itself is a record of execution. Never collect hidden reasoning, system instructions, secrets, or unrelated terminal history. Redact sensitive values in public logs and record the redaction.
7. Explain in Egyptian Arabic, keeping code and repository documentation in English. Use my Django knowledge as a bridge. Explain the reason for each important design choice with a real file/function and a failure it prevents.
8. At the end of an implementation stage, run its checks, update docs/STATE.md, docs/requirements_matrix.md and applicable AI logs, and checkpoint only intended changes in Git. Do not stage everything blindly. Local commits are authorized; publishing is reserved for Stage 15.
9. Finish each stage with: completed work; real commands/results; remaining issues/assumptions; changed file/function pointers; three short comprehension questions without answers; and the next stage number. Stop there. Do not begin the next stage until I request it.

DO NOW
Read the PDF. Initialize the workspace and state/log files. Summarize the selected exercises and missing specifications in plain Arabic. Write a first requirement inventory with PDF page references. Record that the original views specification, Trial Balance mockup, and example documentation repository link are not provided; do not pretend to have read them. Explain the difference between an Odoo addon, model, view, action, and wizard using Django analogies. Do not implement business features yet. End with the standard stage report.
```

## Assistant intermediate messages (verbatim, in order)

1. I'll extract the kit's `prompts/` and `reference/` folders, then read the Stage 00 prompt.
2. The kit has already been extracted (the zip and the root PDF copy are gone), so the PDF is now at `reference/assessment.pdf`. Next I'll read the Stage 00 prompt and pull the PDF text page by page so I can cite page numbers.
3. I've read the whole assessment (pages 9–14 are POS only, which is out of scope). Next I'll check git state and create the `solution/` workspace.
4. Now I'll fix the two kit-root `CLAUDE.md` lines that went stale when the kit was extracted.
5. Before the first commit I need your decision on the author identity, because this history goes public in Stage 15.
6. Next I'll write the Stage 00 AI log and commit it.

Note on message 3: pages 1–8 were read in full; pages 9–14 were only skimmed (opening lines and a keyword search) to confirm they contain nothing but the POS exercise. The final response states this precisely.

## Question asked by the assistant, and the user's answer (verbatim)

**Question:** Commits in solution/ become public on GitHub in Stage 15. Your global git identity is "fahimnox <mohamed.fahim@noxholding.com>", which is your work email. Which identity should I set for this repository only?

- Global identity — Commit as fahimnox <mohamed.fahim@noxholding.com>. The work email will be visible in the public history.
- Don't commit yet — Leave the Stage 00 files uncommitted. You choose an identity before Stage 01, and I commit then.

**User's answer:** Global identity

## Summary of tool activity (summary, not verbatim)

1. Ran `unzip -n Odoo_Assessment_AI_Kit.zip`. It failed because the archive no longer existed; the kit had already been extracted and the zip removed.
2. Listed the kit directory, read `prompts/00_operating_contract.txt`, and extracted the PDF text page by page with `pdftotext`.
3. Confirmed with `git rev-parse` that the kit root is not inside any git repository, and that `solution/` did not exist yet.
4. Wrote `AGENTS.md`, `docs/STATE.md`, `docs/requirements_matrix.md`, `docs/assumptions.md`, `docs/ai/README.md`, `docs/ai/pre_stage_init.md`, `.gitignore` and `.gitattributes`.
5. Edited the kit's `CLAUDE.md` (outside this repository) to point at `reference/assessment.pdf` and drop the zip reference.
6. Ran `git init -b main` in `solution/`, staged the eight files by name, and committed them as `50c1465` using the global identity.
7. Wrote this log with placeholders for the instruction file and the final response. The assistant's turn ended at this point, before the log was completed or committed.
8. After the user's `resume` (below), completed the final-response section, inserted the instruction file text verbatim with a short Python script, and committed this log separately.

## User message after the interruption (verbatim)

```text
resume
```

## Assistant final response (verbatim)

Everything between the two rules below is the final visible response.

---

## Stage 00 — خلصت

قريت الـPDF (صفحات 1–8 كاملة، وصفحات 9–14 فحصتها بس وطلعت كلها POS)، وعملت `solution/` كمستودع git محلي فيه عقد الشغل، وملفات الحالة، وأول جرد للمتطلبات (64 بند بأرقام الصفحات)، وسجل الـAI. مفيش أي business feature اتنفذت.

### التمرينين اللي اخترناهم

**Exercise 1 — `azk_odoo_partner_monitor` (ص 2–6).** موديول بيسحب بيانات شركاء Odoo من صفحة الـPartners الرسمية بـ`requests` و`BeautifulSoup` عن طريق cron يومي، ويخزنها في 4 موديلات: الدول، والشركاء، وتاريخ تغيّر الـstatus، والـreferences. المطلوب منه:
- يسجّل أول ظهور لكل شريك، وكل ترقية أو تنزيل في الـstatus، وكل reference اتضافت أو اختفت.
- لو شريك أو دولة فشلوا، الباقي يكمّل عادي. الأخطاء كلها تتسجل، ويتبعت message في الـchatter لمستخدم ينفع يتغيّر من الإعدادات.
- اتنين cron منفصلين للتحقق: واحد للدول اللي عدد شركائها مش مطابق، وواحد للشركاء اللي عدد الـreferences بتاعتهم مش مطابق.
- لما يطلب دولة فاضية، الموقع بيرجّع كل الشركاء. عشان كده أي لينك شريك من غير `?country_id=` يتجاهل، وأي دولة اختفت من القايمة تبقى `active = False`.
- dashboard هو أول شاشة في الموديول، فيه 4 charts بنفس الفلاتر (Status, Country, Year First Seen).
- الـREADME يشرح إزاي الشغل يستحمل الانقطاع، ويكمّل من غير ما يعيد اللي خلص، ويسحب المتغير بس على قد ما يقدر.

**Exercise 2 — Dynamic Trial Balance (ص 6–8).** wizard (TransientModel) فيه فلاتر: prefixes للحسابات، وjournal، وanalytic account، وتضمين القيود الـdraft (مش الملغية)، وhierarchy وsubtotals، وparents-only لحد level 5، وإخفاء الحسابات الصفرية، وعمود amount currency. كل حساب يطلع له رصيد افتتاحي، وحركة الفترة، ورصيد ختامي، وكل واحد منهم Debit وCredit وBalance. وله 3 مخرجات: Preview جوه Odoo، وPDF، وXLSX. ولازم يبقى معاه demo/test data (قيود posted وdraft، وعملات وanalytic مختلفة، وشجرة حسابات عميقة) واختبارات بتتأكد من الحسابات على dataset معروف.

**Exercise 3 (POS):** مش هنعمله. الـPDF طالب اتنين بس من التلاتة (ص 3).

### الناقص من الـPDF

التلات حاجات دول مش موجودين معانا، ومقريتهمش. متسجلين في `docs/assumptions.md` (M-01..M-03):
1. **الـviews specification الأصلي (ص 4):** المطلوب نعمل الـviews "المذكورة في الـspecification الأصلي" بنفس الفلاتر والـgroupings والـpivots. هنقترح الـviews بنفسنا في Stage 02 ونسجلها كافتراض.
2. **الـmockup بتاع الـTrial Balance (ص 6):** الـwizard المفروض يبقى "as shown in the provided mockup". وكمان قايمة الحقول مفيهاش تواريخ ولا شركة، مع إن الـPDF طالب "selected date range" في الـheader (ص 7).
3. **`azk_zkteco_machine_proxy` (ص 1):** مذكور كمثال لتوثيق كويس، من غير لينك ولا ملف.

وفيه 7 نقط غامضة (D-01..D-07) هتتحسم في Stage 02. أهمهم:
- الـJournals والـAnalytic Accounts نوعهم Many2One، بس الـhelp text بتاعهم بصيغة الجمع.
- الـbuckets المقترحة (<5, 5-10, 11-25, 25+) فيها فجوة بين 10 و11 للقيم الكسرية، وتداخل عند 25.
- الـPDF بيقارن بـ"TB" و"Odoo's dynamic reports". لازم نتأكد من الـsource هو يقصد أنهي تقرير، وهل التقرير ده موجود في Community أصلًا.

### Addon وModel وView وAction وWizard بالمقارنة مع Django

| Odoo | أقرب حاجة في Django | الفرق المهم |
|---|---|---|
| **Addon / Module** | Django app | الـ`__manifest__.py` فيه الاعتماديات وملفات الـXML/CSV اللي هتتحمّل بالترتيب. الموديول بيتثبت **على كل database لوحدها** من Apps أو بـ`-i`، مش من `INSTALLED_APPS`. ومفيش `makemigrations`: الـORM بيعمل الجداول ويعدّلها وقت الـinstall أو الـupdate. |
| **Model** | `models.Model` | اسمه string زي `azk_odoo_partner_monitor.partner`، وجدوله `azk_odoo_partner_monitor_partner`. أي موديول تاني يقدر يوسّعه بـ`_inherit`. و`self` غالبًا **recordset**: حاجة شبه الـQuerySet، بس الـmethods بتشتغل عليه مباشرة. |
| **View** | **مش** Django view. أقرب لـtemplate مع إعدادات `ModelAdmin` | XML بيوصف شكل الشاشة (list/form/search/pivot/graph)، ومتخزن في الـDB، ومفيهوش business logic. بعض أسماء الـtags والـattributes اتغيرت بين الإصدارات، فهنتأكد منها من source الـ18 قبل ما نكتب XML. |
| **Action** | سطر في الـURLconf مع إعدادات generic view | سجل بيقول "افتح موديل X بالـviews دي والفلتر ده". الـmenu بيشاور على action. وفيه أنواع: window، وreport (للـPDF)، وserver، وclient. |
| **Wizard** | Django `Form` عادي (مش ModelForm) جوه dialog | ده `TransientModel`: بيتخزن مؤقت، وOdoo بيمسحه كل شوية. فلاتر الـTrial Balance مكانها هنا، لكن تاريخ الشركاء لأ، لأنه لازم يفضل محفوظ. |

في مشروعنا السلسلة هتبقى كده: `menu → action → dashboard/list`. وفي الـTrial Balance: `menu → action → wizard → Preview/PDF/XLSX → calculation engine`، يعني محرك حساب واحد للتلات مخرجات.

### الأوامر اللي اتشغلت ونتايجها

| الأمر | النتيجة |
|---|---|
| `unzip -n Odoo_Assessment_AI_Kit.zip` | **FAIL**: الـzip مكانش موجود. الكيت كان متفكوك والـzip اتشال، وأنا اعتمدت على حالة الفولدر من جلسة `/init` من غير ما أراجع. الغلطة دي متسجلة في `docs/ai/README.md`. |
| `ls` للفولدر | `prompts/` و`reference/assessment.pdf` موجودين |
| `pdftotext -layout -f N -l N reference/assessment.pdf -` | صفحات 1–8 اتقرت كاملة. صفحات 9–14 اتفحصت بس، واتأكدت إنها كلها POS (خارج النطاق) |
| `git rev-parse --is-inside-work-tree` في فولدر الكيت | مش جوه أي مستودع، فـ`solution/` مش متداخل في repo تاني |
| `git init -b main` جوه `solution/` | PASS |
| `git add` لـ8 ملفات بأساميهم + `git commit` | PASS: الـcommit `50c1465` باسم `fahimnox <mohamed.fahim@noxholding.com>`، حسب الاختيار |
| `git commit` للـlog ده (`docs/ai/stage_00.md`) | PASS: commit تاني في `git log`. الـturn وقف قبل الخطوة دي، واتكمّلت بعد رسالة «resume» |

Tests: **NOT RUN**، لأن المرحلة دي مفيهاش كود.

### اللي لسه مفتوح
- Odoo 18 Community لسه افتراض (A-02)، ومحتاج تأكيد من التيم ليد (Q-01).
- اسم الموديول التاني `azk_dynamic_trial_balance` افتراض (A-03).
- النقط الغامضة D-01..D-07 هتتحسم في Stage 02.
- إيميل الشغل هيبقى ظاهر في الـhistory لما ننشر في Stage 15. ده اختيار متسجل، ولو اتغيّر لازم يتغيّر قبل النشر.
- لسه متفحصش Docker/WSL، ولا PostgreSQL، ولا wkhtmltopdf، ولا الـRAM والـdisk. ده شغل Stage 01.

### الملفات
- `solution/AGENTS.md`: العقد الدائم (النطاق، والـ9 قواعد، وملفات الحالة، والممنوع يدخل git)
- `solution/docs/requirements_matrix.md`: 64 بند (G, P, T, X) بأرقام الصفحات
- `solution/docs/assumptions.md`: المدخلات الناقصة M-01..M-03، والافتراضات A-01..A-03، والغموض D-01..D-07، وأسئلة التيم ليد Q-01..Q-03
- `solution/docs/STATE.md`: كل مرحلة وصلت لفين، والخطوة الجاية، ومعلومات الجهاز اللي اتأكدنا منها لحد دلوقتي
- `solution/docs/ai/README.md` و`pre_stage_init.md` و`stage_00.md`: سجل الـAI
- `solution/.gitignore` و`solution/.gitattributes` (التاني بيوحّد نهايات السطور على LF، لأن الشغل على Windows)
- برّه المستودع: `CLAUDE.md` في فولدر الكيت، اتصلّح فيه مسار الـPDF واتشال كلام الـzip.

### أسئلة جاهزة للتيم ليد (هنكمل بالافتراضات لحد ما ييجي رد)

```text
1. Is Odoo 18 Community acceptable for Exercises 1 and 2?
2. Can you share the original views specification, the Trial Balance wizard mockup, and the azk_zkteco_machine_proxy documentation link?
3. Should the Trial Balance match a specific existing report exactly (opening balances / fiscal year, analytic filtering), or is documented ledger-based behavior acceptable?
```

### أسئلة فهم
1. لما المستخدم يدوس على menu «Partners» في موديولنا، إيه السلسلة اللي بتحصل لحد ما تظهر list الشركاء؟ وأنهي حلقة فيها اللي بتحدد الموديل والفلتر؟
2. ليه الـPDF طالب model مستقل للدول بدل `res.country` اللي موجود في Odoo؟ وإيه اللي ممكن يبوظ لو استخدمنا الموجود؟
3. لو الـscraper طلب دولة مفيهاش شركاء ورجعله كل الشركاء، إيه اللي هيبوظ في الداتا لو صدّقنا النتيجة دي؟

**المرحلة الجاية: Stage 01**

```text
Read prompts/01_environment.txt and execute Stage 01 only, following solution/AGENTS.md.
```

---
