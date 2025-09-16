"""
Custom OpenAI Responses API agent loop implementation
Based on omniparser but with fixes for Responses API compatibility
"""

import json
from typing import Any

import litellm
from agent.decorators import register_agent
from agent.loops.base import AsyncAgentConfig

# Import required types and utilities from agent package
from agent.types import AgentCapability, Tools

SOM_TOOL_SCHEMA = {
    "type": "function",
    "name": "computer",
    "description": "Control a computer by taking screenshots and interacting with UI elements. This tool shows screenshots with numbered elements overlaid on them. Each UI element has been assigned a unique ID number that you can see in the image. Use the element's ID number to interact with any element instead of pixel coordinates.",
    "parameters": {
        "type": "object",
        "properties": {
            "action": {
                "type": "string",
                "enum": [
                    "screenshot",
                    "click",
                    "double_click",
                    "drag",
                    "type",
                    "keypress",
                    "scroll",
                    "move",
                    "wait",
                    "get_current_url",
                    "get_dimensions",
                    "get_environment",
                ],
                "description": "The action to perform",
            },
            "element_id": {
                "type": "integer",
                "description": "The ID of the element to interact with (required for click, double_click, move, scroll actions, and as start/end for drag)",
            },
            "start_element_id": {
                "type": "integer",
                "description": "The ID of the element to start dragging from (required for drag action)",
            },
            "end_element_id": {
                "type": "integer",
                "description": "The ID of the element to drag to (required for drag action)",
            },
            "text": {
                "type": "string",
                "description": "The text to type (required for type action)",
            },
            "keys": {
                "type": "string",
                "description": "Key combination to press (required for keypress action). Single key for individual key press, multiple keys for combinations (e.g., 'ctrl+c')",
            },
            "button": {
                "type": "string",
                "description": "The mouse button to use for click action (left, right, wheel, back, forward) Default: left",
            },
            "scroll_x": {
                "type": "integer",
                "description": "Horizontal scroll amount for scroll action (positive for right, negative for left)",
            },
            "scroll_y": {
                "type": "integer",
                "description": "Vertical scroll amount for scroll action (positive for down, negative for up)",
            },
        },
        "required": ["action"],
    },
}

OMNIPARSER_AVAILABLE = False
try:
    from som import OmniParser

    OMNIPARSER_AVAILABLE = True
except ImportError:
    pass
OMNIPARSER_SINGLETON = None


def get_parser():
    global OMNIPARSER_SINGLETON
    if OMNIPARSER_SINGLETON is None:
        OMNIPARSER_SINGLETON = OmniParser()
    return OMNIPARSER_SINGLETON


def get_last_computer_call_output(messages: list[dict[str, Any]]) -> dict[str, Any] | None:
    """Get the last computer_call_output message from a messages list.

    Args:
        messages: List of messages to search through

    Returns:
        The last computer_call_output message dict, or None if not found
    """
    for message in reversed(messages):
        if isinstance(message, dict) and message.get("type") == "computer_call_output":
            return message
    return None


def _prepare_tools_for_omniparser(tool_schemas: list[dict[str, Any]]) -> tuple[Tools, dict]:
    """Prepare tools for OpenAI API format"""
    omniparser_tools = []
    id2xy = dict()

    for schema in tool_schemas:
        if schema["type"] == "computer":
            omniparser_tools.append(SOM_TOOL_SCHEMA)
            if "id2xy" in schema:
                id2xy = schema["id2xy"]
            else:
                schema["id2xy"] = id2xy
        elif schema["type"] == "function":
            # Function tools use OpenAI-compatible schema directly (liteLLM expects this format)
            # Schema should be: {type, name, description, parameters}
            omniparser_tools.append({"type": "function", **schema["function"]})

    return omniparser_tools, id2xy


async def replace_function_with_computer_call(
    item: dict[str, Any], id2xy: dict[int, tuple[float, float]]
):
    item_type = item.get("type")

    def _get_xy(element_id: int | None) -> tuple[float, float] | tuple[None, None]:
        if element_id is None:
            return (None, None)
        return id2xy.get(element_id, (None, None))

    if item_type == "function_call":
        fn_name = item.get("name")
        fn_args = json.loads(item.get("arguments", "{}"))

        item_id = item.get("id")
        call_id = item.get("call_id")

        if fn_name == "computer":
            action = fn_args.get("action")
            element_id = fn_args.get("element_id")
            start_element_id = fn_args.get("start_element_id")
            end_element_id = fn_args.get("end_element_id")
            text = fn_args.get("text")
            keys = fn_args.get("keys")
            button = fn_args.get("button")
            scroll_x = fn_args.get("scroll_x")
            scroll_y = fn_args.get("scroll_y")

            # Debug: Log the keys value and type
            if action == "keypress":
                print(f"DEBUG: Original keys value: {keys!r}, type: {type(keys)}")
                if keys:
                    print(f"DEBUG: Keys content: '{keys}'")
                else:
                    print(f"DEBUG: Keys is empty or None: {keys}")

            # Convert keys string to array format expected by agent framework
            if action == "keypress" and keys:
                # Split keys by + to create array format that agent expects
                # E.g., "command+spacebar" becomes ["command", "spacebar"]
                keys_array = keys.split("+") if isinstance(keys, str) else keys
                print(f"DEBUG: Converted keys to array: {keys_array}")
            else:
                keys_array = keys

            x, y = _get_xy(element_id)
            start_x, start_y = _get_xy(start_element_id)
            end_x, end_y = _get_xy(end_element_id)

            action_args = {
                "type": action,
                "x": x,
                "y": y,
                "start_x": start_x,
                "start_y": start_y,
                "end_x": end_x,
                "end_y": end_y,
                "text": text,
                "keys": keys_array,
                "button": button,
                "scroll_x": scroll_x,
                "scroll_y": scroll_y,
            }
            # Remove None values to keep the JSON clean
            action_args = {k: v for k, v in action_args.items() if v is not None}

            return [
                {
                    "type": "computer_call",
                    "action": action_args,
                    "id": item_id,
                    "call_id": call_id,
                    "status": "completed",
                }
            ]

    return [item]


async def replace_computer_call_with_function(
    item: dict[str, Any], xy2id: dict[tuple[float, float], int]
):
    """
    Convert computer_call back to function_call format.
    Also handles computer_call_output -> function_call_output conversion.

    Args:
        item: The item to convert
        xy2id: Mapping from (x, y) coordinates to element IDs
    """
    item_type = item.get("type")

    def _get_element_id(x: float | None, y: float | None) -> int | None:
        """Get element ID from coordinates, return None if coordinates are None"""
        if x is None or y is None:
            return None
        return xy2id.get((x, y))

    if item_type == "computer_call":
        action_data = item.get("action", {})

        # Debug: Log the reverse conversion process
        if action_data.get("type") == "keypress":
            print(f"DEBUG REVERSE: computer_call action_data: {action_data}")
            print(f"DEBUG REVERSE: keys from action_data: {action_data.get('keys')!r}")

        # Extract coordinates and convert back to element IDs
        element_id = _get_element_id(action_data.get("x"), action_data.get("y"))
        start_element_id = _get_element_id(action_data.get("start_x"), action_data.get("start_y"))
        end_element_id = _get_element_id(action_data.get("end_x"), action_data.get("end_y"))

        # Convert keys array back to string for API
        keys_value = action_data.get("keys")
        if action_data.get("type") == "keypress" and isinstance(keys_value, list):
            # Convert array back to string: ["command", "spacebar"] -> "command+spacebar"
            keys_string = "+".join(keys_value) if keys_value else ""
            print(
                f"DEBUG REVERSE: Converted keys array {keys_value} back to string: '{keys_string}'"
            )
        else:
            keys_string = keys_value

        # Build function arguments
        fn_args = {
            "action": action_data.get("type"),
            "element_id": element_id,
            "start_element_id": start_element_id,
            "end_element_id": end_element_id,
            "text": action_data.get("text"),
            "keys": keys_string,
            "button": action_data.get("button"),
            "scroll_x": action_data.get("scroll_x"),
            "scroll_y": action_data.get("scroll_y"),
        }

        # Debug: Log function args before cleanup
        if action_data.get("type") == "keypress":
            print(f"DEBUG REVERSE: fn_args before cleanup: {fn_args}")

        # Remove None values to keep the JSON clean
        fn_args = {k: v for k, v in fn_args.items() if v is not None}

        # Debug: Log function args after cleanup
        if action_data.get("type") == "keypress":
            print(f"DEBUG REVERSE: fn_args after cleanup: {fn_args}")
            print(f"DEBUG REVERSE: JSON args will be: {json.dumps(fn_args)}")

        return [
            {
                "type": "function_call",
                "name": "computer",
                "arguments": json.dumps(fn_args),
                "id": item.get("id"),
                "call_id": item.get("call_id"),
                "status": "completed",
            }
        ]

    elif item_type == "computer_call_output":
        output_data = item.get("output")

        # Create the function_call_output
        function_call_output = {
            "type": "function_call_output",
            "call_id": item.get("call_id"),
            "output": json.dumps(output_data),
            "id": item.get("id"),
            "status": "completed",
        }

        # If this is an image output, add a user message with the image for proper LLM processing
        if isinstance(output_data, dict) and output_data.get("type") == "input_image":
            function_call_output["output"] = "input_image"
            user_image_message = {
                "role": "user",
                "content": [output_data],
            }
            return [function_call_output, user_image_message]

        return [function_call_output]

    return [item]


@register_agent(models=r"omniparser\+.*|omni\+.*", priority=100)
class OmniparserConfig(AsyncAgentConfig):
    """Omniparser agent configuration implementing AsyncAgentConfig protocol."""

    async def predict_step(
        self,
        messages: list[dict[str, Any]],
        model: str,
        tools: list[dict[str, Any]] | None = None,
        max_retries: int | None = None,
        stream: bool = False,
        computer_handler=None,
        use_prompt_caching: bool | None = False,
        _on_api_start=None,
        _on_api_end=None,
        _on_usage=None,
        _on_screenshot=None,
        **kwargs,
    ) -> dict[str, Any]:
        """
        OpenAI computer-use-preview agent loop using liteLLM responses.

        Supports OpenAI's computer use preview models.
        """
        print("DEBUG: USING OUR CUSTOM OMNIPARSER FORK!")
        if not OMNIPARSER_AVAILABLE:
            raise ValueError(
                "omniparser loop requires som to be installed. Install it with `pip install cua-som`."
            )

        tools = tools or []

        llm_model = model.split("+")[-1]

        # Prepare tools for OpenAI API
        openai_tools, id2xy = _prepare_tools_for_omniparser(tools)

        # Find last computer_call_output
        last_computer_call_output = get_last_computer_call_output(messages)  # type: ignore
        if last_computer_call_output:
            image_url = last_computer_call_output.get("output", {}).get("image_url", "")
            image_data = image_url.split(",")[-1]
            if image_data:
                parser = get_parser()
                result = parser.parse(image_data)
                if _on_screenshot:
                    await _on_screenshot(result.annotated_image_base64, "annotated_image")
                for element in result.elements:
                    id2xy[element.id] = (
                        (element.bbox.x1 + element.bbox.x2) / 2,
                        (element.bbox.y1 + element.bbox.y2) / 2,
                    )

        # handle computer calls -> function calls
        # Create reverse mapping for coordinate to ID conversion
        xy2id = {v: k for k, v in id2xy.items()}

        new_messages = []
        for message in messages:
            if not isinstance(message, dict):
                message = message.__dict__
            new_messages += await replace_computer_call_with_function(message, xy2id)  # type: ignore
        messages = new_messages

        # Prepare API call kwargs
        api_kwargs = {
            "model": llm_model,
            "input": messages,
            "tools": openai_tools if openai_tools else None,
            "stream": stream,
            "truncation": "auto",
            "num_retries": max_retries,
            **kwargs,
        }

        # Call API start hook
        if _on_api_start:
            await _on_api_start(api_kwargs)

        print(str(api_kwargs)[:1000])

        # Use liteLLM responses
        response = await litellm.aresponses(**api_kwargs)

        # Call API end hook
        if _on_api_end:
            await _on_api_end(api_kwargs, response)

        # Extract usage information
        usage = {
            **response.usage.model_dump(),  # type: ignore
            "response_cost": response._hidden_params.get("response_cost", 0.0),  # type: ignore
        }
        if _on_usage:
            await _on_usage(usage)

        # handle som function calls -> xy computer calls
        new_output = []
        for i in range(len(response.output)):  # type: ignore
            original_item = response.output[i].model_dump()  # type: ignore

            # Debug: Log before conversion
            if original_item.get("name") == "computer":
                args = json.loads(original_item.get("arguments", "{}"))
                if args.get("action") == "keypress":
                    print(f"DEBUG: Before conversion - keys: {args.get('keys')!r}")

            converted_items = await replace_function_with_computer_call(original_item, id2xy)

            # Debug: Log after conversion
            for converted in converted_items:
                if (
                    converted.get("type") == "computer_call"
                    and converted.get("action", {}).get("type") == "keypress"
                ):
                    print(
                        f"DEBUG: After conversion - keys: {converted.get('action', {}).get('keys')!r}"
                    )
                    print(f"DEBUG: Full converted computer_call: {json.dumps(converted, indent=2)}")

            # Debug: Log what we're adding to new_output
            if any(
                item.get("type") == "computer_call"
                and item.get("action", {}).get("type") == "keypress"
                for item in converted_items
            ):
                print(
                    f"DEBUG: Adding to new_output - items with keypress: {len([item for item in converted_items if item.get('type') == 'computer_call' and item.get('action', {}).get('type') == 'keypress'])}"
                )

            new_output += converted_items

        # Debug: Log final output structure
        keypress_items = [
            item
            for item in new_output
            if item.get("type") == "computer_call"
            and item.get("action", {}).get("type") == "keypress"
        ]
        if keypress_items:
            print(f"DEBUG: FINAL OUTPUT - Found {len(keypress_items)} keypress items")
            for item in keypress_items:
                print(
                    f"DEBUG: FINAL OUTPUT - keypress keys: {item.get('action', {}).get('keys')!r}"
                )

        return {"output": new_output, "usage": usage}

    async def predict_click(
        self, model: str, image_b64: str, instruction: str, **kwargs
    ) -> tuple[float, float] | None:
        """
        Predict click coordinates using OmniParser and LLM.

        Uses OmniParser to annotate the image with element IDs, then uses LLM
        to identify the correct element ID based on the instruction.
        """
        if not OMNIPARSER_AVAILABLE:
            return None

        # Parse the image with OmniParser to get annotated image and elements
        parser = get_parser()
        result = parser.parse(image_b64)

        # Extract the LLM model from composed model string
        llm_model = model.split("+")[-1]

        # Create system prompt for element ID prediction
        SYSTEM_PROMPT = """
You are an expert UI element locator. Given a GUI image annotated with numerical IDs over each interactable element, along with a user's element description, provide the ID of the specified element.

The image shows UI elements with numbered overlays. Each number corresponds to a clickable/interactable element.

Output only the element ID as a single integer.
""".strip()

        # Prepare messages for LLM
        messages = [
            {"role": "system", "content": SYSTEM_PROMPT},
            {
                "role": "user",
                "content": [
                    {
                        "type": "image_url",
                        "image_url": {
                            "url": f"data:image/png;base64,{result.annotated_image_base64}"
                        },
                    },
                    {"type": "text", "text": f"Find the element: {instruction}"},
                ],
            },
        ]

        # Call LLM to predict element ID
        response = await litellm.acompletion(
            model=llm_model, messages=messages, max_tokens=10, temperature=0.1
        )

        # Extract element ID from response
        response_text = response.choices[0].message.content.strip()  # type: ignore

        # Try to parse the element ID
        try:
            element_id = int(response_text)

            # Find the element with this ID and return its center coordinates
            for element in result.elements:
                if element.id == element_id:
                    center_x = (element.bbox.x1 + element.bbox.x2) / 2
                    center_y = (element.bbox.y1 + element.bbox.y2) / 2
                    return (center_x, center_y)
        except ValueError:
            # If we can't parse the ID, return None
            pass

        return None

    def get_capabilities(self) -> list[AgentCapability]:
        """Return the capabilities supported by this agent."""
        return ["step", "click"]
