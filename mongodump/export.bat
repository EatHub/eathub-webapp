@echo off

set OUT_DIR=exported_json
for %%x in (webapp_recipe, webapp_profile, auth_user, webapp_country, webapp_food_type, webapp_language, webapp_special_condition, webapp_temporality) do (
  mongoexport -d eathub -c %%x -o %OUT_DIR%/%%x.json.tmp --jsonArray
  python -m json.tool %OUT_DIR%/%%x.json.tmp>%OUT_DIR%/%%x.json
  rm %OUT_DIR%/%%x.json.tmp
)

set x=ajax_uploadedimage
mongoexport -d eathub -c %x% -o %OUT_DIR%/%x%.json.tmp --jsonArray -q "{image: {$regex: '.+\.persist\..+'}}"
python -m json.tool %OUT_DIR%/%x%.json.tmp>%OUT_DIR%/%x%.json
rm %OUT_DIR%/%x%.json.tmp
