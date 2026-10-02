#!/usr/bin/env python3

import argparse
import hashlib
import json
import os
import sys
from pathlib import Path


# ============================================================
# CONFIGURATION
# ============================================================

BUTTON_TEXT = "შეამოწმე პასუხი"

WRONG_TEXT = "არასწორია, კიდევ სცადეთ!"

CORRECT_TEXT = "სწორია!"

OUTPUT_FILE = str(Path(__file__).resolve().parent / "docs" / "index.html")


# ============================================================
# ENCRYPTION / OBFUSCATION
# ============================================================
#
# This is intended to hide the answer and revealed text from
# casual inspection of the HTML source.
#
# It is NOT intended as strong security. Because answers are
# only 1-6 digits, a determined person could brute-force them.
#
# The entered answer + random salt are used to generate a
# SHA-256 based byte stream, which is XORed with the UTF-8
# message.
# ============================================================


def generate_keystream(answer: str, salt: bytes, length: int) -> bytes:
    output = bytearray()
    counter = 0

    while len(output) < length:
        block = hashlib.sha256(
            answer.encode("utf-8")
            + salt
            + counter.to_bytes(4, "big")
        ).digest()

        output.extend(block)
        counter += 1

    return bytes(output[:length])


def encrypt_message(answer: str, message: str):
    plaintext = message.encode("utf-8")
    salt = os.urandom(16)

    keystream = generate_keystream(
        answer,
        salt,
        len(plaintext)
    )

    encrypted = bytes(
        a ^ b
        for a, b in zip(plaintext, keystream)
    )

    return salt.hex(), encrypted.hex()


# ============================================================
# HTML GENERATOR
# ============================================================


def generate_html(answer: str, success_message: str) -> str:

    answer_hash = hashlib.sha256(
        answer.encode("utf-8")
    ).hexdigest()

    salt_hex, encrypted_message_hex = encrypt_message(
        answer,
        success_message
    )

    # json.dumps safely escapes strings for insertion into
    # JavaScript.
    button_text_js = json.dumps(BUTTON_TEXT)
    wrong_text_js = json.dumps(WRONG_TEXT)
    correct_text_js = json.dumps(CORRECT_TEXT)

    return f"""<!DOCTYPE html>
<html lang="en">
<head>
<meta charset="UTF-8">

<meta
    name="viewport"
    content="width=device-width, initial-scale=1, maximum-scale=1"
>

<title>Enter Code</title>

<style>

* {{
    box-sizing: border-box;
}}

html,
body {{
    margin: 0;
    padding: 0;
    width: 100%;
    height: 100%;
}}

body {{
    font-family:
        -apple-system,
        BlinkMacSystemFont,
        "Segoe UI",
        Roboto,
        Helvetica,
        Arial,
        sans-serif;

    background: white;
    color: black;

    display: flex;
    justify-content: center;
    align-items: center;

    padding: 24px;
}}

.container {{
    width: 100%;
    max-width: 360px;
    text-align: center;
}}

input {{
    display: block;

    width: 100%;
    height: 58px;

    font-size: 28px;
    text-align: center;

    padding: 8px 12px;

    border: 2px solid #999;
    border-radius: 8px;

    outline: none;
}}

input:focus {{
    border-color: #333;
}}

button {{
    display: block;

    width: 100%;
    height: 54px;

    margin-top: 16px;

    font-size: 18px;

    border: 0;
    border-radius: 8px;

    background: #222;
    color: white;

    cursor: pointer;
}}

button:active {{
    transform: scale(0.98);
}}

#status {{
    margin-top: 20px;

    font-size: 18px;
    font-weight: 600;

    min-height: 24px;
}}

#message {{
    margin-top: 16px;

    font-size: 18px;
    line-height: 1.5;

    color: black;

    white-space: pre-wrap;
    overflow-wrap: anywhere;
}}

</style>
</head>

<body>

<div class="container">

    <input
        id="answer"
        type="text"
        inputmode="numeric"
        pattern="[0-9]*"
        maxlength="6"
        autocomplete="off"
        autocorrect="off"
        spellcheck="false"
        aria-label="Answer"
    >

    <button id="checkButton"></button>

    <div id="status"></div>

    <div id="message"></div>

</div>


<script>

const ANSWER_HASH =
    "{answer_hash}";

const SALT_HEX =
    "{salt_hex}";

const ENCRYPTED_MESSAGE_HEX =
    "{encrypted_message_hex}";


const BUTTON_TEXT = {button_text_js};

const WRONG_TEXT = {wrong_text_js};

const CORRECT_TEXT = {correct_text_js};


const input =
    document.getElementById("answer");

const button =
    document.getElementById("checkButton");

const status =
    document.getElementById("status");

const message =
    document.getElementById("message");


button.textContent = BUTTON_TEXT;


/*
    Prevent anything except digits from remaining
    in the field, and limit input to six digits.
*/

input.addEventListener("input", () => {{

    input.value = input.value
        .replace(/[^0-9]/g, "")
        .slice(0, 6);

}});


/*
    Allow the keyboard Enter / Go button to submit.
*/

input.addEventListener("keydown", event => {{

    if (event.key === "Enter") {{
        checkAnswer();
    }}

}});


button.addEventListener(
    "click",
    checkAnswer
);


function hexToBytes(hex) {{

    const bytes =
        new Uint8Array(hex.length / 2);

    for (
        let i = 0;
        i < bytes.length;
        i++
    ) {{
        bytes[i] =
            parseInt(
                hex.substr(i * 2, 2),
                16
            );
    }}

    return bytes;
}}


function bytesToHex(bytes) {{

    return Array
        .from(bytes)
        .map(
            byte =>
                byte
                    .toString(16)
                    .padStart(2, "0")
        )
        .join("");
}}


async function sha256Bytes(bytes) {{

    const hash =
        await crypto.subtle.digest(
            "SHA-256",
            bytes
        );

    return new Uint8Array(hash);
}}


async function sha256Text(text) {{

    const encoded =
        new TextEncoder().encode(text);

    const hash =
        await sha256Bytes(encoded);

    return bytesToHex(hash);
}}


async function makeKeystream(
    answer,
    salt,
    requiredLength
) {{

    const encoder =
        new TextEncoder();

    const answerBytes =
        encoder.encode(answer);

    const result = [];

    let counter = 0;


    while (
        result.length < requiredLength
    ) {{

        const counterBytes =
            new Uint8Array(4);

        new DataView(
            counterBytes.buffer
        ).setUint32(
            0,
            counter,
            false
        );


        const data =
            new Uint8Array(
                answerBytes.length
                + salt.length
                + counterBytes.length
            );


        data.set(
            answerBytes,
            0
        );

        data.set(
            salt,
            answerBytes.length
        );

        data.set(
            counterBytes,
            answerBytes.length
            + salt.length
        );


        const block =
            await sha256Bytes(data);


        for (
            const byte of block
        ) {{

            if (
                result.length
                >= requiredLength
            ) {{
                break;
            }}

            result.push(byte);
        }}

        counter++;
    }}


    return new Uint8Array(result);
}}


async function decryptMessage(answer) {{

    const salt =
        hexToBytes(SALT_HEX);

    const encrypted =
        hexToBytes(
            ENCRYPTED_MESSAGE_HEX
        );


    const keystream =
        await makeKeystream(
            answer,
            salt,
            encrypted.length
        );


    const decrypted =
        new Uint8Array(
            encrypted.length
        );


    for (
        let i = 0;
        i < encrypted.length;
        i++
    ) {{

        decrypted[i] =
            encrypted[i]
            ^ keystream[i];
    }}


    return new TextDecoder(
        "utf-8"
    ).decode(decrypted);
}}


async function checkAnswer() {{

    const answer =
        input.value;


    /*
        Empty input is simply treated as incorrect.
    */

    const enteredHash =
        await sha256Text(answer);


    if (
        enteredHash !== ANSWER_HASH
    ) {{

        status.textContent =
            WRONG_TEXT;

        status.style.color =
            "red";

        message.textContent =
            "";

        return;
    }}


    const revealedMessage =
        await decryptMessage(answer);


    status.textContent =
        CORRECT_TEXT;

    status.style.color =
        "green";

    message.textContent =
        revealedMessage;
}}


input.focus();

</script>

</body>
</html>
"""


# ============================================================
# MAIN
# ============================================================


def main():

    if hasattr(sys.stdout, "reconfigure"):
        sys.stdout.reconfigure(encoding="utf-8")

    parser = argparse.ArgumentParser(
        description=(
            "Generate a mobile-friendly HTML puzzle page."
        )
    )

    parser.add_argument(
        "answer",
        help="Correct numeric answer, maximum 6 digits."
    )

    parser.add_argument(
        "message",
        help="UTF-8 text displayed after the correct answer."
    )

    parser.add_argument(
        "-o",
        "--output",
        default=OUTPUT_FILE,
        help=f"Output HTML file. Default: {OUTPUT_FILE}"
    )

    args = parser.parse_args()


    if not args.answer.isascii() or not args.answer.isdigit():
        parser.error(
            "The answer must contain numbers only."
        )

    if not 1 <= len(args.answer) <= 6:
        parser.error(
            "The answer must be between 1 and 6 digits."
        )


    html = generate_html(
        args.answer,
        args.message
    )


    output_path = Path(args.output)
    output_path.parent.mkdir(parents=True, exist_ok=True)

    output_path.write_text(
        html,
        encoding="utf-8"
    )


    print(
        f"Created: {output_path.resolve()}"
    )


if __name__ == "__main__":
    main()
