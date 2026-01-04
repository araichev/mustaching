import marimo

__generated_with = "0.18.4"
app = marimo.App()


@app.cell
def _():
    import sys

    import pandas as pd
    import marimo as mo

    sys.path.append("../")
    import mustaching as ms

    # magic command not supported in marimo; please file an issue to add support
    # %load_ext autoreload
    # '%autoreload 2' command supported automatically in marimo
    return mo, ms, pd


@app.cell(hide_code=True)
def _(mo):
    mo.md(r"""
    # Load transactions
    """)
    return


@app.cell
def _(ms):
    # Invent some sample transactions.
    transactions = ms.create_transactions("2021-01-01", "2021-12-31")

    # Alternatively, upload your own transactions as say 'my_transactions.csv'
    # transactions = ms.read_transactions('my_transactions.csv')

    transactions.head(10)
    return (transactions,)


@app.cell(hide_code=True)
def _(mo):
    mo.md(r"""
    # Summarize and plot transactions
    """)
    return


@app.cell
def _(mo, ms, pd, transactions):
    def run_demo_1(transactions: pd.DataFrame):
        summary = ms.summarize(
            transactions, freq="QS"
        )  # dictionary of kind -> DataFrame
        for k, v in summary.items():
            mo.output.append(k)
            mo.output.append(v)

        plot = ms.plot(summary, currency="$")
        for k, v in plot.items():  # dictionary of kind -> Plotly figure
            mo.output.append(k)
            mo.output.append(v)

    run_demo_1(transactions)
    return


@app.cell(hide_code=True)
def _(mo):
    mo.md(r"""
    # For transactions without categories we get the following
    """)
    return


@app.cell
def _(mo, ms, pd, transactions):
    def run_demo_2(transactions: pd.DataFrame):
        summary = ms.summarize(transactions.drop("category", axis="columns"), freq="QS")
        for k, v in summary.items():
            mo.output.append(k)
            mo.output.append(v)
        plot = ms.plot(summary, currency="$")
        for k, v in plot.items():  # dictionary of kind -> Plotly figure
            mo.output.append(k)
            mo.output.append(v)

    run_demo_2(transactions)
    return


@app.cell
def _():
    return


if __name__ == "__main__":
    app.run()
