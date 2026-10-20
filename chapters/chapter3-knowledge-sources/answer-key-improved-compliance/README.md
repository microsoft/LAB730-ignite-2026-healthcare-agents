# Chapter 3: improved-compliance answer key

An opt-in, prompt-only alternative to the [standard Chapter 3 answer key](../answer-key/). It makes tool execution and measurement coverage explicit for models that skip segmentation or omit linear dimensions.


## What changes

- A dedicated [Radiology Assistant (EHR)](.github/agents/radiology-assistant-ehr.agent.md) exposes only file reading, search, editing, and the existing `medimageparse` tools. It keeps the existing MAI model selection, has no fallback to unmeasured reporting, and cannot use terminal or subagent tools.
- [write-report-with-ehr](.github/skills/write-report-with-ehr/SKILL.md) requires successful segmentation, cleanup, and description before reporting. FINDINGS has explicit slots for each lesion's two diameters, AP/TR extents, and volumes, plus totals and applicable changes. Required coverage takes precedence over the 250-word target.
- [lookup-patient-history](.github/skills/lookup-patient-history/SKILL.md) permits file reads and limits its no-segmentation rule to the lookup step. It hands control back to the report workflow and does not truncate prior reports to meet a word cap.
- [write-imaging-factsheet-ehr](.github/skills/write-imaging-factsheet-ehr/SKILL.md) and its [template](.github/skills/write-imaging-factsheet-ehr/template/factsheet.md) distinguish diameter fields from the area product, retain measurements below the measurability threshold, and handle zero lesions and explicit unavailable values. They distinguish parent-workflow handoff from standalone output.

The new agent and factsheet helper have distinct filenames and names, so Chapter 1 and Chapter 2's agent and skills remain unchanged. Installing this variant replaces only the two Chapter 3 skills if they are already installed: `lookup-patient-history` and `write-report-with-ehr`. 