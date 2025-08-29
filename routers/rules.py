"""
Financial Compliance Rules Router

This module generates AI-powered compliance rules specifically for monitoring
financial advisor-client conversations to detect potential violations such as:
- Regulation Best Interest breaches
- Elderly abuse indicators
- Suitability violations
- Conflict of interest issues
- Unauthorized trading
- Churning and excessive trading
- Misrepresentation of products
- Inadequate risk disclosure

The generated rules are designed to be used by downstream AI agents for
real-time conversation monitoring and violation flagging.
"""

from fastapi import APIRouter, Depends, HTTPException, status, BackgroundTasks
from fastapi.responses import StreamingResponse
from sqlalchemy.orm import Session
from typing import List, Optional, Generator, Iterator
from pydantic import BaseModel
import json
import os
import asyncio
from llama_index.core import SimpleDirectoryReader

from database import get_db
from models import Rule, Document
from ai import client, MODEL

router = APIRouter()


class RuleGenerateRequest(BaseModel):
    document_id: int
    generated_by: str
    rule_type: Optional[str] = "financial_compliance"
    severity: Optional[str] = "medium"


class RuleResponse(BaseModel):
    id: int
    policy_space_id: str
    document_id: int
    rule_name: str
    rule_description: Optional[str]
    rule_content: dict
    rule_type: str
    severity: str
    generated_by: str
    is_active: bool
    created_at: str
    updated_at: Optional[str]

    class Config:
        from_attributes = True


def read_document_content(file_path: str) -> str:
    """
    Read document content using LlamaIndex for better file format support.
    Supports PDF, DOCX, TXT, MD and other common document formats.
    """
    try:
        if not os.path.exists(file_path):
            raise FileNotFoundError(f"Document file not found: {file_path}")

        # Use LlamaIndex SimpleDirectoryReader to parse the document
        reader = SimpleDirectoryReader(input_files=[file_path], recursive=False)

        documents = reader.load_data()

        if not documents:
            raise ValueError(f"No content could be extracted from file: {file_path}")

        # Combine all document content (in case file is split into multiple documents)
        content = "\n\n".join([doc.text for doc in documents])

        if not content.strip():
            raise ValueError(f"No text content found in file: {file_path}")

        return content

    except FileNotFoundError:
        raise
    except Exception as e:
        # Fallback to basic file reading for unsupported formats
        try:
            with open(file_path, "r", encoding="utf-8") as file:
                content = file.read()
                if content.strip():
                    return content
        except UnicodeDecodeError:
            with open(file_path, "rb") as file:
                content = file.read()
                return content.decode("utf-8", errors="ignore")

        raise ValueError(f"Failed to read document content: {str(e)}")


def get_response_schema() -> dict:
    return {
        "type": "object",
        "properties": {
            "rules": {
                "type": "array",
                "items": {
                    "type": "object",
                    "properties": {
                        "name": {"type": "string"},
                        "description": {"type": "string"},
                        "category": {
                            "type": "string",
                            "enum": [
                                "suitability_violation",
                                "disclosure_failure",
                                "conflict_of_interest",
                                "elderly_abuse",
                                "unauthorized_trading",
                                "misrepresentation",
                                "churning",
                                "best_interest_violation",
                                "unsuitable_recommendation",
                                "inadequate_documentation",
                            ],
                        },
                        "detection_criteria": {
                            "type": "array",
                            "items": {
                                "type": "object",
                                "properties": {
                                    "trigger_phrase": {"type": "string"},
                                    "context_required": {"type": "string"},
                                    "confidence_threshold": {"type": "number"},
                                    "description": {"type": "string"},
                                },
                                "required": ["trigger_phrase", "context_required"],
                            },
                        },
                        "red_flags": {"type": "array", "items": {"type": "string"}},
                        "violation_indicators": {
                            "type": "array",
                            "items": {"type": "string"},
                        },
                        "violation_message": {"type": "string"},
                        "severity": {
                            "type": "string",
                            "enum": ["low", "medium", "high", "critical"],
                        },
                        "regulatory_reference": {"type": "string"},
                        "recommended_action": {"type": "string"},
                    },
                    "required": [
                        "name",
                        "description",
                        "category",
                        "detection_criteria",
                        "red_flags",
                        "violation_indicators",
                        "violation_message",
                        "severity",
                        "regulatory_reference",
                        "recommended_action",
                    ],
                },
            }
        },
        "required": ["rules"],
    }


def generate_rules_with_ai_stream(
    document_content: str, document_name: str
) -> Generator[str, None, None]:
    if not client:
        fallback_response = {
            "rules": [
                {
                    "name": f"Manual Review Rule for {document_name}",
                    "description": f"Placeholder rule for {document_name} - AI client not configured",
                    "category": "best_interest_violation",
                    "detection_criteria": [
                        {
                            "trigger_phrase": "requires manual review",
                            "context_required": "financial advisor-client conversation",
                            "description": f"Requires manual review against {document_name} policies",
                        }
                    ],
                    "red_flags": ["AI client not configured"],
                    "violation_indicators": ["System configuration issue"],
                    "violation_message": f"This conversation requires manual review against {document_name} policies",
                    "severity": "medium",
                    "regulatory_reference": document_name,
                    "recommended_action": "Manual compliance review required",
                }
            ],
        }
        yield json.dumps(fallback_response)
        return

    prompt = f"""
Document Content:
{document_content}

Based ONLY on the above document content, generate violation detection rules for monitoring financial advisor-client conversations. Extract specific requirements, prohibitions, and compliance standards directly from the document text.
    """

    try:
        response_schema = get_response_schema()

        # Use the streaming API correctly
        stream = client.models.generate_content_stream(
            model=MODEL,
            contents=prompt,
            config={
                "response_schema": response_schema,
                "response_mime_type": "application/json",
            },
        )

        # Stream each chunk as it comes, showing real-time progress
        response_chunks = []
        chunk_count = 0
        total_chars = 0

        for chunk in stream:
            if chunk.text:
                chunk_count += 1
                total_chars += len(chunk.text)
                print(f"🔄 Streaming chunk {chunk_count}: {len(chunk.text)} chars")
                response_chunks.append(chunk.text)

                # Yield progress with more detail
                progress_data = {
                    "status": "streaming",
                    "chunk": chunk_count,
                    "total_chars": total_chars,
                    "partial_content": chunk.text[:150].replace("\n", " ") + "...",
                    "timestamp": json.dumps({"time": "now"}),  # Add timestamp for UI
                }
                yield json.dumps(progress_data)

        # Combine all chunks into complete response
        response_text = "".join(response_chunks).strip()
        print(
            f"✅ Streaming completed. Total chunks: {chunk_count}, Total length: {len(response_text)} chars"
        )

        if response_text.startswith("```json"):
            response_text = response_text[7:]
        if response_text.endswith("```"):
            response_text = response_text[:-3]

        parsed_response = json.loads(response_text.strip())
        rules_count = len(parsed_response.get("rules", []))
        print(f"📋 Generated {rules_count} rules")

        # Send parsing completion update
        yield json.dumps(
            {
                "status": "parsing",
                "message": f"Successfully parsed {rules_count} compliance rules",
                "rules_count": rules_count,
            }
        )

        yield json.dumps(parsed_response)

    except Exception as e:
        print(f"❌ Error in AI generation: {str(e)}")
        fallback_response = {
            "rules": [
                {
                    "name": f"Fallback Rule for {document_name}",
                    "description": f"AI-generated compliance rule based on {document_name} due to processing error",
                    "category": "best_interest_violation",
                    "detection_criteria": [
                        {
                            "trigger_phrase": "requires manual review",
                            "context_required": "financial advisor-client conversation",
                            "confidence_threshold": 0.5,
                            "description": f"Requires manual review against {document_name} policies",
                        }
                    ],
                    "red_flags": ["Processing error occurred"],
                    "violation_indicators": [
                        "Unable to process regulation automatically"
                    ],
                    "violation_message": f"This conversation requires review against {document_name} policies",
                    "severity": "medium",
                    "regulatory_reference": document_name,
                    "recommended_action": "Manual compliance review required",
                }
            ],
        }
        yield json.dumps(fallback_response)


def generate_rules_with_ai(document_content: str, document_name: str) -> dict:
    if not client:
        return {
            "rules": [
                {
                    "name": f"Manual Review Rule for {document_name}",
                    "description": f"Placeholder rule for {document_name} - AI client not configured",
                    "category": "best_interest_violation",
                    "detection_criteria": [
                        {
                            "trigger_phrase": "requires manual review",
                            "context_required": "financial advisor-client conversation",
                            "confidence_threshold": 0.5,
                            "description": f"Requires manual review against {document_name} policies",
                        }
                    ],
                    "red_flags": ["AI client not configured"],
                    "violation_indicators": ["System configuration issue"],
                    "violation_message": f"This conversation requires manual review against {document_name} policies",
                    "severity": "medium",
                    "regulatory_reference": document_name,
                    "recommended_action": "Manual compliance review required",
                }
            ],
        }

    prompt = f"""
Document Content:
{document_content}

Based ONLY on the above document content, generate violation detection rules for monitoring financial advisor-client conversations. Extract specific requirements, prohibitions, and compliance standards directly from the document text.

Return ONLY valid JSON in this exact format:
    """

    try:
        response = client.models.generate_content(
            model=MODEL,
            contents=prompt,
            # config={
            #     "response_schema": "",
            #     "response_mime_type": ""
            # }
        )

        response_text = response.text.strip()
        if response_text.startswith("```json"):
            response_text = response_text[7:]
        if response_text.endswith("```"):
            response_text = response_text[:-3]

        return json.loads(response_text.strip())
    except Exception as e:
        return {
            "rules": [
                {
                    "name": f"Fallback Rule for {document_name}",
                    "description": f"AI-generated compliance rule based on {document_name} due to processing error",
                    "category": "best_interest_violation",
                    "detection_criteria": [
                        {
                            "trigger_phrase": "requires manual review",
                            "context_required": "financial advisor-client conversation",
                            "confidence_threshold": 0.5,
                            "description": f"Requires manual review against {document_name} policies",
                        }
                    ],
                    "red_flags": ["Processing error occurred"],
                    "violation_indicators": [
                        "Unable to process regulation automatically"
                    ],
                    "violation_message": f"This conversation requires review against {document_name} policies",
                    "severity": "medium",
                    "regulatory_reference": document_name,
                    "recommended_action": "Manual compliance review required",
                }
            ],
        }


async def save_rules_to_db(
    rules_data: List[dict],
    request: RuleGenerateRequest,
    document: Document,
    db: Session,
) -> List[RuleResponse]:
    created_rules = []

    for rule_data in rules_data:
        db_rule = Rule(
            policy_space_id=document.policy_space_id,
            document_id=document.id,
            rule_name=rule_data.get("name", "Generated Compliance Rule"),
            rule_description=rule_data.get("description", ""),
            rule_content=rule_data,
            rule_type=request.rule_type,
            severity=rule_data.get("severity", request.severity),
            generated_by=request.generated_by,
        )

        db.add(db_rule)
        db.commit()
        db.refresh(db_rule)

        created_rules.append(
            RuleResponse(
                id=db_rule.id,
                policy_space_id=db_rule.policy_space_id,
                document_id=db_rule.document_id,
                rule_name=db_rule.rule_name,
                rule_description=db_rule.rule_description,
                rule_content=db_rule.rule_content,
                rule_type=db_rule.rule_type,
                severity=db_rule.severity,
                generated_by=db_rule.generated_by,
                is_active=db_rule.is_active,
                created_at=db_rule.created_at.isoformat(),
                updated_at=(
                    db_rule.updated_at.isoformat() if db_rule.updated_at else None
                ),
            )
        )

    return created_rules


@router.post("/generate")
async def generate_rules_stream(
    request: RuleGenerateRequest,
    db: Session = Depends(get_db),
):
    document = db.query(Document).filter(Document.id == request.document_id).first()

    if not document:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND, detail="Document not found"
        )

    try:
        document_content = read_document_content(document.file_path)
    except FileNotFoundError:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Document file not found on filesystem",
        )
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Error reading document: {str(e)}",
        )

    def generate_and_save():
        final_response = None
        chunk_count = 0

        try:
            print("🚀 Starting rule generation stream...")
            # Stream the AI response generation
            for chunk in generate_rules_with_ai_stream(
                document_content, document.original_filename
            ):
                chunk_count += 1
                print(f"📤 Yielding chunk {chunk_count} to client")
                # Yield each chunk as it comes
                yield chunk
                yield "\n"  # Add newline for better streaming parsing

                # Parse the chunk to get the final response for saving
                try:
                    chunk_data = json.loads(chunk)
                    if "rules" in chunk_data:
                        final_response = chunk_data
                        print(
                            f"📝 Found final response with {len(chunk_data['rules'])} rules"
                        )
                except json.JSONDecodeError:
                    # If we can't parse this chunk, it might be a progress indicator
                    print(f"🔄 Progress chunk: {chunk[:100]}...")
                    continue

            print(f"✅ Streaming completed. Total chunks: {chunk_count}")

            # Save rules to database after streaming is complete
            if final_response and "rules" in final_response:
                try:
                    print(
                        f"💾 Saving {len(final_response['rules'])} rules to database..."
                    )
                    for rule_data in final_response["rules"]:
                        db_rule = Rule(
                            policy_space_id=document.policy_space_id,
                            document_id=document.id,
                            rule_name=rule_data.get("name", "Generated Rule"),
                            rule_description=rule_data.get("description", ""),
                            rule_content=rule_data,
                            rule_type=request.rule_type,
                            severity=rule_data.get("severity", request.severity),
                            generated_by=request.generated_by,
                        )

                        db.add(db_rule)

                    db.commit()
                    print(
                        f"✅ Successfully saved {len(final_response['rules'])} rules to database"
                    )

                    # Yield completion signal
                    completion_signal = {
                        "status": "completed",
                        "saved_rules": len(final_response["rules"]),
                    }
                    yield f"\n{json.dumps(completion_signal)}\n"

                except Exception as e:
                    # Log error and yield error status
                    error_msg = f"Error saving rules to database: {str(e)}"
                    print(f"❌ {error_msg}")
                    error_signal = {"status": "error", "message": error_msg}
                    yield f"\n{json.dumps(error_signal)}\n"
            else:
                # No valid response received
                error_msg = "No valid rules generated"
                print(f"❌ {error_msg}")
                error_signal = {
                    "status": "error",
                    "message": error_msg,
                }
                yield f"\n{json.dumps(error_signal)}\n"

        except Exception as e:
            # Handle any other errors in the generation process
            error_msg = f"Error in rule generation: {str(e)}"
            print(f"❌ {error_msg}")
            error_signal = {"status": "error", "message": error_msg}
            yield f"\n{json.dumps(error_signal)}\n"

    return StreamingResponse(
        generate_and_save(),
        media_type="application/x-ndjson",  # Use newline-delimited JSON for better streaming
        headers={
            "Cache-Control": "no-cache",
            "Connection": "keep-alive",
            "X-Accel-Buffering": "no",  # Disable nginx buffering
            "Access-Control-Allow-Origin": "*",
            "Access-Control-Allow-Headers": "*",
        },
    )


@router.post("/generate-sync", response_model=List[RuleResponse])
async def generate_rules(
    request: RuleGenerateRequest,
    background_tasks: BackgroundTasks,
    db: Session = Depends(get_db),
):
    document = db.query(Document).filter(Document.id == request.document_id).first()

    if not document:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND, detail="Document not found"
        )

    try:
        document_content = read_document_content(document.file_path)
    except FileNotFoundError:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Document file not found on filesystem",
        )
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Error reading document: {str(e)}",
        )

    try:
        ai_response = generate_rules_with_ai(
            document_content, document.original_filename
        )
        rules_data = ai_response.get("rules", [])

        created_rules = await save_rules_to_db(rules_data, request, document, db)
        return created_rules

    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Error generating financial compliance rules: {str(e)}",
        )


@router.get("/", response_model=List[RuleResponse])
async def get_rules(
    policy_space_id: Optional[str] = None,
    document_id: Optional[int] = None,
    is_active: Optional[bool] = None,
    db: Session = Depends(get_db),
):
    query = db.query(Rule)

    if policy_space_id:
        query = query.filter(Rule.policy_space_id == policy_space_id)
    if document_id:
        query = query.filter(Rule.document_id == document_id)
    if is_active is not None:
        query = query.filter(Rule.is_active == is_active)

    rules = query.order_by(Rule.created_at.desc()).all()

    return [
        RuleResponse(
            id=rule.id,
            policy_space_id=rule.policy_space_id,
            document_id=rule.document_id,
            rule_name=rule.rule_name,
            rule_description=rule.rule_description,
            rule_content=rule.rule_content,
            rule_type=rule.rule_type,
            severity=rule.severity,
            generated_by=rule.generated_by,
            is_active=rule.is_active,
            created_at=rule.created_at.isoformat(),
            updated_at=rule.updated_at.isoformat() if rule.updated_at else None,
        )
        for rule in rules
    ]


@router.get("/{rule_id}", response_model=RuleResponse)
async def get_rule(rule_id: int, db: Session = Depends(get_db)):
    rule = db.query(Rule).filter(Rule.id == rule_id).first()

    if not rule:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND, detail="Rule not found"
        )

    return RuleResponse(
        id=rule.id,
        policy_space_id=rule.policy_space_id,
        document_id=rule.document_id,
        rule_name=rule.rule_name,
        rule_description=rule.rule_description,
        rule_content=rule.rule_content,
        rule_type=rule.rule_type,
        severity=rule.severity,
        generated_by=rule.generated_by,
        is_active=rule.is_active,
        created_at=rule.created_at.isoformat(),
        updated_at=rule.updated_at.isoformat() if rule.updated_at else None,
    )


@router.put("/{rule_id}/toggle")
async def toggle_rule_status(rule_id: int, db: Session = Depends(get_db)):
    rule = db.query(Rule).filter(Rule.id == rule_id).first()

    if not rule:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND, detail="Rule not found"
        )

    rule.is_active = not rule.is_active
    db.commit()
    db.refresh(rule)

    return {
        "message": f"Rule {rule_id} {'activated' if rule.is_active else 'deactivated'}"
    }


@router.delete("/{rule_id}")
async def delete_rule(rule_id: int, db: Session = Depends(get_db)):
    rule = db.query(Rule).filter(Rule.id == rule_id).first()

    if not rule:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND, detail="Rule not found"
        )

    db.delete(rule)
    db.commit()

    return {"message": f"Rule {rule_id} deleted successfully"}


@router.delete("/policy-space/{policy_space_id}")
async def delete_rules_by_policy_space(
    policy_space_id: str, db: Session = Depends(get_db)
):
    # Check if policy space exists by checking if any rules exist for it
    rules = db.query(Rule).filter(Rule.policy_space_id == policy_space_id).all()

    if not rules:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"No rules found for policy space '{policy_space_id}'",
        )

    # Count rules before deletion
    rule_count = len(rules)

    # Delete all rules for the policy space
    deleted_count = (
        db.query(Rule).filter(Rule.policy_space_id == policy_space_id).delete()
    )
    db.commit()

    return {
        "message": f"Successfully deleted {deleted_count} rules for policy space '{policy_space_id}'",
        "deleted_count": deleted_count,
        "policy_space_id": policy_space_id,
    }
