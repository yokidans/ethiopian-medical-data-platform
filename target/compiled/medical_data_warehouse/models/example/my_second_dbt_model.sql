-- Use the `ref` function to select from other models

select *
from "medical_data_warehouse"."4"."my_first_dbt_model"
where id = 1