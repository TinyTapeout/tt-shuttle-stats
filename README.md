# Shuttle stats for TT04 and beyond

![stats](tt_shuttles.png)

# SQL

    select
      id as project_id,
      top_module,
      shuttle_id,
      first_submission_time
    from
      public.projects
    where
      status = 'submitted'
    order by
      shuttle_id desc,
      first_submission_time desc;

