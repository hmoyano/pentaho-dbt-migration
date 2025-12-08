CREATE OR REPLACE FUNCTION TFSES_ANALYTICS.TFS_SILVER.GETENUMML("ENUMERATIONID" NUMBER(38,0), "MULTILANGUAGEID" NUMBER(38,0))
RETURNS VARCHAR
LANGUAGE SQL
AS '
SELECT COALESCE(
    (SELECT t.translation
     FROM TFS_BRONZE.MILES_TRANSLATEDSTRING t
     WHERE t.language_id = MultilanguageId
       AND t.multilanguagestring_id = s.description_mlid
     LIMIT 1),
    (SELECT t.translation
     FROM TFS_BRONZE.MILES_LANGUAGE l
     JOIN TFS_BRONZE.MILES_TRANSLATEDSTRING t
       ON l.parentlanguage_id = t.language_id
     WHERE l.language_id = MultilanguageId
       AND t.multilanguagestring_id = s.description_mlid
     LIMIT 1),
    s.description
)
FROM TFS_BRONZE.MILES_SYSENUMERATION s
WHERE s.sysenumeration_id = EnumerationId
LIMIT 1
';