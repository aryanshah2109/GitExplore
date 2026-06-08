"""Single-page Streamlit frontend for GitExplore."""

from __future__ import annotations

import os
from urllib.parse import urlparse

import requests
import streamlit as st


API_BASE_URL = os.getenv("GITEXPLORE_API_BASE_URL", "http://localhost:8000").rstrip("/")


def api_url(path: str) -> str:
    return f"{API_BASE_URL}{path}"


def repo_name_from_url(repo_url: str) -> str:
    parsed = urlparse(repo_url.strip())
    return parsed.path.rstrip("/").split("/")[-1] if parsed.path else repo_url.strip()


def post_json(path: str, payload: dict) -> dict:
    response = requests.post(api_url(path), json=payload, timeout=600)
    response.raise_for_status()
    return response.json()


def delete_request(path: str) -> dict:
    response = requests.delete(api_url(path), timeout=60)
    response.raise_for_status()
    return response.json()


st.set_page_config(page_title="GitExplore", page_icon="⚡", layout="wide")
st.title("GitExplore")
st.caption("Query any GitHub repository with AI")

st.session_state.setdefault("repo_id", "")
st.session_state.setdefault("repo_name", "")
st.session_state.setdefault("answer", "")
st.session_state.setdefault("judgement", None)
st.session_state.setdefault("query_type", "")

with st.sidebar:
    st.header("Ingest Repository")
    repo_url = st.text_input("GitHub URL", placeholder="https://github.com/user/repo")
    branch = st.text_input("Branch", value="main")

    if st.button("Ingest", use_container_width=True):
        if not repo_url.strip():
            st.error("Enter a GitHub repository URL.")
        else:
            try:
                with st.spinner("Ingesting repository..."):
                    result = post_json(
                        "/api/v1/ingest",
                        {"repo_url": repo_url.strip(), "branch": branch.strip() or "main"},
                    )
                st.session_state.repo_id = result["repo_id"]
                st.session_state.repo_name = repo_name_from_url(repo_url)
                st.success(f"Indexed {result['file_count']} files into {result['chunk_count']} chunks.")
            except Exception as e:
                st.error(str(e))

    if st.session_state.get("repo_id"):
        st.success(f"Active: {st.session_state.get('repo_name')}")
        if st.button("Clear Session", use_container_width=True):
            try:
                delete_request(f"/api/v1/session/{st.session_state['repo_id']}")
                st.session_state.repo_id = ""
                st.session_state.repo_name = ""
                st.session_state.answer = ""
                st.session_state.judgement = None
                st.session_state.query_type = ""
                st.success("Session cleared.")
            except Exception as e:
                st.error(str(e))

query = st.text_input(
    "Ask something about the repository",
    disabled=not bool(st.session_state.get("repo_id")),
)
ask_btn = st.button("Ask", disabled=not bool(st.session_state.get("repo_id")), type="primary")

if ask_btn:
    if not query.strip():
        st.error("Enter a question.")
    else:
        try:
            with st.spinner("Searching codebase..."):
                result = post_json(
                    "/api/v1/query",
                    {"repo_id": st.session_state["repo_id"], "query": query.strip()},
                )
            st.session_state.answer = result["answer"]
            st.session_state.judgement = result["judgement"]
            st.session_state.query_type = result.get("query_type", "")
        except Exception as e:
            st.error(str(e))

if st.session_state.get("answer"):
    st.markdown(st.session_state["answer"])

    with st.expander("Answer Quality Scores"):
        judgement = st.session_state.get("judgement") or {}
        col1, col2, col3, col4 = st.columns(4)
        col1.metric("Faithfulness", judgement.get("faithfulness", 0))
        col2.metric("Retrieval Relevance", judgement.get("retrieval_relevance", 0))
        col3.metric("Citation Accuracy", judgement.get("citation_accuracy", 0))
        col4.metric("Query Type Fit", judgement.get("query_type_fit", 0))

    with st.expander("Judge Reasoning"):
        st.write((st.session_state.get("judgement") or {}).get("reasoning", ""))

