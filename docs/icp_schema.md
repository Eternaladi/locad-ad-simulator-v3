# ICP schema

Raw files must contain:

```json
{
  "meta": {},
  "icps": []
}
```

The compiler writes one normalized atom per ICP to `data/icp/compiled/icp_atoms.jsonl`. Required fields include `icp_id`, `region`, `persona`, `product_category`, `sales_channels`, `top_pain_points`, `locad_value_propositions`, and `likely_objections`.
