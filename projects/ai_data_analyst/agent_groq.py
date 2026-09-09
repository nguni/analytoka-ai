import json
import os

from dotenv import load_dotenv
from groq import Groq

from tools.data_tools import (
    inspect_dataset,
    get_dataset_sample,
    get_column_statistics,
    group_and_aggregate,
    sort_and_rank,
)

from tools.analysis_tools import (
    exploratory_analysis,
    correlation_analysis,
    detect_outliers,
    analyze_distribution,
    analyze_time_series,
)

from tools.chart_tools import (
    create_chart,
)


# ============================================================
# 1. LOAD ENVIRONMENT
# ============================================================

load_dotenv()

def get_groq_api_key():

    # Streamlit Cloud
    try:
        return st.secrets["GROQ_API_KEY"]

    except Exception:
        pass

    # Local development
    return os.getenv("GROQ_API_KEY")


api_key = get_groq_api_key()


if not api_key:
    raise ValueError(
        "GROQ_API_KEY was not found."
    )


client = Groq(
    api_key=api_key
)

# ============================================================
# 2. TOOL REGISTRY
# ============================================================

tool_registry = {
    "inspect_dataset": inspect_dataset,
    "get_dataset_sample": get_dataset_sample,
    "get_column_statistics": get_column_statistics,
    "group_and_aggregate": group_and_aggregate,
    "sort_and_rank": sort_and_rank,
    "exploratory_analysis": exploratory_analysis,
    "correlation_analysis": correlation_analysis,
    "detect_outliers": detect_outliers,
    "analyze_distribution": analyze_distribution,
    "analyze_time_series": analyze_time_series,
    "create_chart": create_chart,
}


# ============================================================
# 3. TOOL SCHEMAS
# ============================================================

tools = [

    # --------------------------------------------------------
    # INSPECT DATASET
    # --------------------------------------------------------

    {
        "type": "function",
        "function": {
            "name": "inspect_dataset",
            "description": (
                "Inspect dataset structure including columns, data types, "
                "missing values and duplicates."
            ),
            "parameters": {
                "type": "object",
                "properties": {
                    "file_path": {
                        "type": "string"
                    },
                    "sheet_name": {
                        "type": "string"
                    }
                },
                "required": [
                    "file_path"
                ]
            }
        }
    },


    # --------------------------------------------------------
    # DATASET SAMPLE
    # --------------------------------------------------------

    {
        "type": "function",
        "function": {
            "name": "get_dataset_sample",
            "description": (
                "Return sample rows from the dataset to understand "
                "the meaning of columns and values."
            ),
            "parameters": {
                "type": "object",
                "properties": {
                    "file_path": {
                        "type": "string"
                    },
                    "sheet_name": {
                        "type": "string"
                    },
                    "rows": {
                        "type": "integer"
                    }
                },
                "required": [
                    "file_path"
                ]
            }
        }
    },


    # --------------------------------------------------------
    # COLUMN STATISTICS
    # --------------------------------------------------------

    {
        "type": "function",
        "function": {
            "name": "get_column_statistics",
            "description": (
                "Calculate descriptive statistics for one column."
            ),
            "parameters": {
                "type": "object",
                "properties": {
                    "file_path": {
                        "type": "string"
                    },
                    "sheet_name": {
                        "type": "string"
                    },
                    "column": {
                        "type": "string"
                    }
                },
                "required": [
                    "file_path",
                    "column"
                ]
            }
        }
    },


    # --------------------------------------------------------
    # GROUP + AGGREGATE
    # --------------------------------------------------------

    {
        "type": "function",
        "function": {
            "name": "group_and_aggregate",
            "description": (
                "Group rows by a categorical column and calculate "
                "a metric using sum, mean, median, min, max or count."
            ),
            "parameters": {
                "type": "object",
                "properties": {
                    "file_path": {
                        "type": "string"
                    },
                    "sheet_name": {
                        "type": "string"
                    },
                    "group_by": {
                        "type": "string"
                    },
                    "metric": {
                        "type": "string"
                    },
                    "aggregation": {
                        "type": "string",
                        "enum": [
                            "sum",
                            "mean",
                            "median",
                            "min",
                            "max",
                            "count"
                        ]
                    }
                },
                "required": [
                    "file_path",
                    "group_by",
                    "metric",
                    "aggregation"
                ]
            }
        }
    },


    # --------------------------------------------------------
    # SORT AND RANK
    # --------------------------------------------------------

    {
        "type": "function",
        "function": {
            "name": "sort_and_rank",
            "description": (
                "Rank records from highest to lowest or lowest to highest."
            ),
            "parameters": {
                "type": "object",
                "properties": {
                    "file_path": {
                        "type": "string"
                    },
                    "sheet_name": {
                        "type": "string"
                    },
                    "column": {
                        "type": "string"
                    },
                    "ascending": {
                        "type": "boolean"
                    },
                    "limit": {
                        "type": "integer"
                    }
                },
                "required": [
                    "file_path",
                    "column"
                ]
            }
        }
    },


    # --------------------------------------------------------
    # EXPLORATORY ANALYSIS
    # --------------------------------------------------------

    {
        "type": "function",
        "function": {
            "name": "exploratory_analysis",
            "description": (
                "Perform broad exploratory data analysis including "
                "numeric summaries, categorical summaries, missing values "
                "and duplicate detection."
            ),
            "parameters": {
                "type": "object",
                "properties": {
                    "file_path": {
                        "type": "string"
                    },
                    "sheet_name": {
                        "type": "string"
                    }
                },
                "required": [
                    "file_path"
                ]
            }
        }
    },


    # --------------------------------------------------------
    # CORRELATION ANALYSIS
    # --------------------------------------------------------

    {
        "type": "function",
        "function": {
            "name": "correlation_analysis",
            "description": (
                "Analyze correlations and relationships between "
                "numeric columns."
            ),
            "parameters": {
                "type": "object",
                "properties": {
                    "file_path": {
                        "type": "string"
                    },
                    "sheet_name": {
                        "type": "string"
                    },
                    "threshold": {
                        "type": "number"
                    }
                },
                "required": [
                    "file_path"
                ]
            }
        }
    },


    # --------------------------------------------------------
    # OUTLIER ANALYSIS
    # --------------------------------------------------------

    {
        "type": "function",
        "function": {
            "name": "detect_outliers",
            "description": (
                "Detect outliers in a numeric column using the IQR method."
            ),
            "parameters": {
                "type": "object",
                "properties": {
                    "file_path": {
                        "type": "string"
                    },
                    "sheet_name": {
                        "type": "string"
                    },
                    "column": {
                        "type": "string"
                    }
                },
                "required": [
                    "file_path",
                    "column"
                ]
            }
        }
    },


    # --------------------------------------------------------
    # DISTRIBUTION ANALYSIS
    # --------------------------------------------------------

    {
        "type": "function",
        "function": {
            "name": "analyze_distribution",
            "description": (
                "Analyze the statistical distribution of a numeric column."
            ),
            "parameters": {
                "type": "object",
                "properties": {
                    "file_path": {
                        "type": "string"
                    },
                    "sheet_name": {
                        "type": "string"
                    },
                    "column": {
                        "type": "string"
                    }
                },
                "required": [
                    "file_path",
                    "column"
                ]
            }
        }
    },


    # --------------------------------------------------------
    # TIME SERIES
    # --------------------------------------------------------

    {
        "type": "function",
        "function": {
            "name": "analyze_time_series",
            "description": (
                "Analyze how a numeric metric changes over time."
            ),
            "parameters": {
                "type": "object",
                "properties": {
                    "file_path": {
                        "type": "string"
                    },
                    "sheet_name": {
                        "type": "string"
                    },
                    "date_column": {
                        "type": "string"
                    },
                    "metric": {
                        "type": "string"
                    },
                    "aggregation": {
                        "type": "string",
                        "enum": [
                            "sum",
                            "mean",
                            "median",
                            "min",
                            "max",
                            "count"
                        ]
                    },
                    "period": {
                        "type": "string",
                        "enum": [
                            "day",
                            "week",
                            "month",
                            "quarter",
                            "year"
                        ]
                    }
                },
                "required": [
                    "file_path",
                    "date_column",
                    "metric"
                ]
            }
        }
    },


    # --------------------------------------------------------
    # CHART GENERATOR
    # --------------------------------------------------------

    {
        "type": "function",
        "function": {
            "name": "create_chart",
            "description": (
                "Create a visualization from the current dataset. "
                "Supports bar, line, scatter, histogram, boxplot, pie "
                "and correlation heatmap."
            ),
            "parameters": {
                "type": "object",
                "properties": {
                    "file_path": {
                        "type": "string"
                    },
                    "sheet_name": {
                        "type": "string"
                    },
                    "chart_type": {
                        "type": "string",
                        "enum": [
                            "bar",
                            "line",
                            "scatter",
                            "histogram",
                            "boxplot",
                            "pie",
                            "correlation_heatmap"
                        ]
                    },
                    "x_column": {
                        "type": "string"
                    },
                    "y_column": {
                        "type": "string"
                    },
                    "aggregation": {
                        "type": "string",
                        "enum": [
                            "sum",
                            "mean",
                            "median",
                            "count",
                            "min",
                            "max"
                        ]
                    },
                    "period": {
                        "type": "string",
                        "enum": [
                            "day",
                            "week",
                            "month",
                            "quarter",
                            "year"
                        ]
                    },
                    "title": {
                        "type": "string"
                    }
                },
                "required": [
                    "file_path",
                    "chart_type"
                ]
            }
        }
    }
]


# ============================================================
# 4. MAIN AGENT FUNCTION
# ============================================================

def run_agent(
    question: str,
    file_path: str,
    sheet_name: str = None
) -> dict:

    """
    Main AI Data Analyst agent.

    Returns:

    {
        "answer": "...",
        "charts": [...]
    }
    """

    system_prompt = f"""
You are a professional AI Data Analyst.

CURRENT DATASET
File: {file_path}
Worksheet: {sheet_name}

Your responsibility is to perform reliable data analysis
using the available Python tools.

IMPORTANT RULES

1. Never invent numbers or dataset values.

2. Python tools must perform calculations.
   You interpret and explain the results.

3. If you do not understand the dataset structure,
   call inspect_dataset first.

4. If column meaning is unclear,
   call get_dataset_sample.

5. Column names are normalized internally.

6. For broad requests such as:
   - analyze this dataset
   - perform exploratory analysis
   - give me key insights

   use exploratory_analysis.

7. For grouped business questions such as:
   - revenue by region
   - average salary by department
   - tickets by agent

   use group_and_aggregate.

8. For correlations,
   use correlation_analysis.

9. For unusual numeric observations,
   use detect_outliers.

10. For numeric distributions,
    use analyze_distribution.

11. For date/time trends,
    use analyze_time_series.

12. If the user asks for a chart, graph, plot,
    visualization or visual comparison,
    call create_chart.

13. Choose visualizations appropriately:

    bar:
    category comparisons

    line:
    time trends

    scatter:
    relationship between numeric variables

    histogram:
    numeric distribution

    boxplot:
    outliers and spread

    pie:
    simple part-to-whole comparisons with few categories

    correlation_heatmap:
    relationships between multiple numeric variables

14. You may call several tools in sequence.

15. Give concise but useful explanations.

16. Highlight business implications where appropriate.

17. Always analyze the currently selected worksheet.
"""

    messages = [
        {
            "role": "system",
            "content": system_prompt
        },
        {
            "role": "user",
            "content": question
        }
    ]

    charts = []

    max_steps = 12


    # ========================================================
    # AGENT LOOP
    # ========================================================

    for step in range(max_steps):

        print(
            f"\n--- Agent step {step + 1} ---"
        )


        # ----------------------------------------------------
        # CALL GROQ
        # ----------------------------------------------------

        try:

            response = (
                client.chat.completions.create(
                    model="openai/gpt-oss-120b",
                    messages=messages,
                    tools=tools,
                    tool_choice="auto"
                )
            )

        except Exception as error:

            return {
                "answer": (
                    f"Groq API error: {error}"
                ),
                "charts": charts
            }


        assistant_message = (
            response
            .choices[0]
            .message
        )


        # ----------------------------------------------------
        # NO TOOL CALL = FINAL RESPONSE
        # ----------------------------------------------------

        if not assistant_message.tool_calls:

            final_answer = (
                assistant_message.content
                or
                "Analysis completed."
            )

            return {
                "answer": final_answer,
                "charts": charts
            }


        # ----------------------------------------------------
        # SAVE ASSISTANT TOOL REQUEST
        # ----------------------------------------------------

        messages.append(
            {
                "role": "assistant",
                "content": (
                    assistant_message.content
                ),
                "tool_calls": [
                    {
                        "id": tool_call.id,
                        "type": "function",
                        "function": {
                            "name": (
                                tool_call
                                .function
                                .name
                            ),
                            "arguments": (
                                tool_call
                                .function
                                .arguments
                            )
                        }
                    }
                    for tool_call
                    in assistant_message.tool_calls
                ]
            }
        )


        # ----------------------------------------------------
        # EXECUTE TOOLS
        # ----------------------------------------------------

        for tool_call in (
            assistant_message
            .tool_calls
        ):

            tool_name = (
                tool_call
                .function
                .name
            )


            # ------------------------------------------------
            # READ TOOL ARGUMENTS
            # ------------------------------------------------

            try:

                arguments = json.loads(
                    tool_call
                    .function
                    .arguments
                )

            except Exception:

                arguments = {}


            # ------------------------------------------------
            # FORCE CURRENT DATASET
            # ------------------------------------------------

            arguments[
                "file_path"
            ] = file_path


            if sheet_name is not None:

                arguments[
                    "sheet_name"
                ] = sheet_name


            print(
                "Tool:",
                tool_name
            )

            print(
                "Arguments:",
                arguments
            )


            # ------------------------------------------------
            # FIND FUNCTION
            # ------------------------------------------------

            tool_function = (
                tool_registry.get(
                    tool_name
                )
            )


            if tool_function is None:

                result = {
                    "error": (
                        f"Unknown tool: {tool_name}"
                    )
                }


            else:

                # --------------------------------------------
                # EXECUTE FUNCTION
                # --------------------------------------------

                try:

                    result = (
                        tool_function(
                            **arguments
                        )
                    )


                    # ----------------------------------------
                    # COLLECT GENERATED CHART
                    # ----------------------------------------

                    if (
                        tool_name
                        ==
                        "create_chart"
                        and
                        isinstance(
                            result,
                            dict
                        )
                        and
                        result.get(
                            "path"
                        )
                    ):

                        charts.append(
                            result
                        )


                    print(
                        "Result:",
                        result
                    )


                except Exception as error:

                    result = {
                        "error": str(
                            error
                        )
                    }

                    print(
                        "Tool error:",
                        error
                    )


            # ------------------------------------------------
            # SEND TOOL RESULT BACK TO MODEL
            # ------------------------------------------------

            messages.append(
                {
                    "role": "tool",
                    "tool_call_id": (
                        tool_call.id
                    ),
                    "content": json.dumps(
                        result,
                        default=str
                    )
                }
            )


    # ========================================================
    # MAX STEPS
    # ========================================================

    return {
        "answer": (
            "The analysis reached the maximum "
            "number of tool steps."
        ),
        "charts": charts
    }