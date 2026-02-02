def generate_table_description(table_name, metadata, profile):
    prompt = f"""
    Table Name: {table_name}
    Columns: {metadata}
    Data Quality: {profile}

    Explain this table in business-friendly language.
    """
    return prompt  # later connect LLM
