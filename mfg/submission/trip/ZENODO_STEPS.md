# Zenodo steps for the author (TRIP requires data and code in a repository, with a link at submission)

I cannot create the DOI (no Zenodo credentials). Everything to upload is in `mfg/submission/trip/zenodo/`:
`mfg_carriers_replication_v1.zip` (the archive), `.zenodo.json` (metadata; hidden file, use `ls -a`), `README.md`, `NOTICE`,
`LICENSE`, `LICENSE-DATA` (copies of the files inside the zip).

1. Sign in at https://zenodo.org (an ORCID login works) and click Upload, then New upload.
2. Drop `mfg_carriers_replication_v1.zip` into the file area (size is about 70 MB; the Zenodo limit is 50 GB).
3. Fill the form from `.zenodo.json`:
   - Resource type: Software (the file says `upload_type: software`; choose Dataset instead if you prefer; the files are the same).
   - Title, Publication date (2026-11-19, or the day you publish), Creators: Dang, Quang-Vinh; affiliation British University Vietnam; ORCID 0000-0002-3877-8024.
   - Description: paste the `description` text. Keywords: the seven in the file. Language: English. Version: 1.0.
   - Licence: choose MIT (Zenodo allows one licence; the mixed licences are stated in the description and in `LICENSE-DATA` and `NOTICE`).
   - Related works: add the three links of `related_identifiers` ("is derived from"). Later add the paper (see step 7).
   - Access: Open.
4. In the DOI field choose "No, I need a DOI" and click "Reserve DOI" (Zenodo shows the DOI before publishing). Copy it.
5. Decide when to publish. Options: (a) publish now, which makes the files public and fixes the DOI; or (b) leave the record as a draft until
   acceptance: the reserved DOI stays valid but resolves only after publication, and a draft is not reachable by reviewers.
   TRIP asks for a link at submission, so publish before submitting if you do not want to explain its absence. The manuscript is
   single anonymized review: publishing exposes your name next to the data, which does not matter in that model; the anonymous manuscript
   itself says the link is withheld. If you prefer, use the draft's private preview link only for the editor.
6. Put the DOI into: `title_page.docx` data-availability line (replace "Zenodo DOI: to be added"), the Data availability section of the
   non-anonymous manuscript (rebuild with `mfg/submission/trip/` scripts after editing `ZENODO_DOI` in `trip_config.py`), and the
   submission-system data field.
7. After the paper is accepted, edit the Zenodo record (published records can be edited without a new DOI for metadata) and add a related
   identifier "is supplement to" with the article DOI.
8. Check `NOTICE`: if you do not wish to redistribute the OpenStreetMap-derived city files, delete `data/processed` from the zip before
   uploading and say in the README that they are rebuilt from the BBBike extracts with `src/ccu/geo.py` (the tests then need those files).

Decisions for you: (i) licence of the code is MIT here, while the GitHub repository carries Apache-2.0; (ii) whether to publish the
derived OpenStreetMap files under ODbL (included now); (iii) Software or Dataset as resource type.
