# Logical Input Schema

Data kind: **time_series**

Required logical fields:

- `source_or_trigger_id`
- `time`
- `measurement`
- `uncertainty`
- `quality_flags`
- `background_or_auxiliary_series`
- `instrument_or_channel`

Map archive-specific names to these logical fields in a versioned configuration file. Fail clearly when a required field is absent.
