Run the full digest pipeline: fetcher → scorer → summarizer → renderer → emailer.

Execute `python run.py` and monitor the output. If any stage fails, diagnose the error and suggest a fix. After completion, report:
- How many items were fetched (new vs duplicates)
- How many sources succeeded vs failed
- Which output files were generated in `outputs/`
