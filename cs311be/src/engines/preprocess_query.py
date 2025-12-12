from fast_langdetect import detect
import re
from llama_index.llms.azure_openai import AzureOpenAI
# from src.prompts.chatbot_prompt import add_tone_marks_prompt
from dotenv import load_dotenv
import os
from difflib import SequenceMatcher
from pydantic import BaseModel
from typing import Literal, Optional, Tuple, Dict, Any, List
from llama_index.core.program import LLMTextCompletionProgram
from src.engines.llm_engine import LLMEngine


class QueryOutput(BaseModel):
    query_str: str
    lang: Literal["Tiếng Việt", "Tiếng Anh", "Others"]


class TextPreprocessor:
    def __init__(self):
        load_dotenv()
        # Các viết tắt phổ biến trong phỏng vấn IT và kỹ thuật
        self.abbreviation_dict = {
            # General IT
            "cntt": "công nghệ thông tin",
            "it": "it",
            "fe": "front end",
            "be": "back end",
            "fullstack": "full stack",
            "devops": "devops",
            "sdlc": "software development life cycle",
            # Programming paradigms / CS
            "oop": "object oriented programming",
            "fp": "functional programming",
            "dsa": "data structures and algorithms",
            # Web / Protocols
            "api": "api",
            "rest": "rest",
            "graphql": "graphql",
            "http": "http",
            "tcp/ip": "tcp ip",
            # Databases
            "rdbms": "relational database",
            "nosql": "nosql",
            "sql": "sql",
            # Cloud / CI-CD / Containers
            "ci/cd": "ci cd",
            "cicd": "ci cd",
            "k8s": "kubernetes",
            "kubernetes": "kubernetes",
            "docker": "docker",
            "aws": "aws",
            "gcp": "gcp",
            "azure": "azure",
            # Languages / Frameworks (common aliases)
            "js": "javascript",
            "ts": "typescript",
            "py": "python",
            "rb": "ruby",
            "cpp": "c++",
            "csharp": "c#",
            "cs": "c#",
            "reactjs": "react",
            "nodejs": "node.js",
            "nestjs": "nest.js",
            "nextjs": "next.js",
            "vuejs": "vue.js",
            "springboot": "spring boot",
            # AI/ML
            "ml": "machine learning",
            "dl": "deep learning",
            "ai": "artificial intelligence",
            "cv": "computer vision",
            "nlp": "natural language processing",
            "rl": "reinforcement learning",
            "sklearn": "scikit learn",
            # Ops / Misc
            "os": "operating system",
            "linux": "linux",
            "git": "git",
        }
        self.short_chat = [
            # short_chat term
            "chào bạn",
            "chào bạn",
            "chaofo bạn",
            "chao ban",
            "hello",
            "hi",
            "xin chào",
            "xin chao",
            "hihi",
            "haha",
            "hoho",
            "hehe",
            "lol",
            "kk",
            "xin chào",
            "chào",
            "hello",
            "hi",
            "bạn khỏe không",
            "ban khoe khong",
            "khỏe không",
            "khoe khong",
            "dạ vâng",
            "da vang",
            "vâng",
            "vang",
            "cảm ơn bạn",
            "cam on ban",
            "cảm ơn",
            "cam on",
            "thank you",
            "thanks",
            "haha",
            "hihi",
            "hoho",
            "hehe",
            "lol",
            "kk",
            "đúng rồi",
            "dung roi",
            "đúng",
            "dung",
            "tạm biệt",
            "tam biet",
            "bye",
            "goodbye",
            "uh huh",
            "uhm",
            "uh",
            "uhhuh",
            "ồ thật sao",
            "o that sao",
            "thật sao",
            "that sao",
            "thế à",
            "the a",
            "thật à",
            "that a",
            "ồ",
            "o",
            "wow",
            "woww",
            "wowww",
            "ừ",
            "u",
            "ừm",
            "um",
            "dạ",
            "da",
            "ok",
            "okay",
        ]
        self.config = LLMEngine()
        self.llm = self.config.llm2
        # self.program = self.init_program()
        self.INTAB = "ạảãàáâậầấẩẫăắằặẳẵóòọõỏôộổỗồốơờớợởỡéèẻẹẽêếềệểễúùụủũưựữửừứíìịỉĩýỳỷỵỹđ" \
                     "ẠẢÃÀÁÂẬẦẤẨẪĂẮẰẶẲẴÓÒỌÕỎÔỘỔỖỒỐƠỜỚỢỞỠÉÈẺẸẼÊẾỀỆỂỄÚÙỤỦŨƯỰỮỬỪỨÍÌỊỈĨÝỲỶỴỸĐ"


    def replace_abbreviations(self, text):
        words = text.split()
        replaced_words = [
            self.abbreviation_dict.get(word.lower(), word) for word in words
        ]
        return " ".join(replaced_words)
    
    def detect_short_chat(self, text):
        normalized_text = text.lower().strip()
        def is_similar(text1, text2, threshold=0.85):
            return SequenceMatcher(None, text1, text2).ratio() >= threshold

        matches_pattern = any(
            is_similar(normalized_text, pattern) for pattern in self.short_chat
        )

        if matches_pattern or len(text.split(" ")) <= 3:
            return (text, 'Tiếng Việt')
        else:
            return False
    
    def language_check(self, text):
        try:
            lang = detect(text)
            if lang['lang'] == 'vi':
                return 'Tiếng Việt'
            elif lang['lang'] == 'en':
                return 'English'
            else:
                return 'Tiếng Việt'
        except Exception as e:
            print(f"Error in language detection: {e}")
            return 'Tiếng Việt'

    def remove_punctuation(self, text):
        return re.sub(r'[^\w\s]', '', text)


    def check_tone_mark(self, text):
        try:
            words = self.remove_punctuation(text).split()
            count = sum(
                all(char not in self.INTAB for char in word) for word in words
            )

            ratio = count / len(words)
            return ratio < 0.7
        except Exception as e:
            print(f"Error in tone mark check: {e}")

    def add_tone_marks(self, text):
        result = self.llm.complete(
            prompt=(
                f"Sửa lỗi chính tả và thêm dấu tiếng Việt cho truy vấn trong bối cảnh phỏng vấn IT: {text}. "
                f"Chỉ trả về câu đã sửa (giữ nguyên thuật ngữ kỹ thuật), không kèm giải thích."
            )
        )
        return result.text

    def translate_to_vn(self, text):
        result = self.llm.complete(
            prompt=(
                f"Dịch sang tiếng Việt trong ngữ cảnh phỏng vấn IT (giữ nguyên thuật ngữ kỹ thuật nếu cần): {text}. "
                f"Chỉ trả về bản dịch, không kèm giải thích."
            )
        )
        return result.text

    def normalize_it_terms(self, text: str) -> str:
        """Chuẩn hóa một số thuật ngữ/viết tắt kỹ thuật để tăng độ chính xác truy vấn."""
        words = text.split()
        normalized: List[str] = []
        for w in words:
            key = w.lower()
            normalized.append(self.abbreviation_dict.get(key, w))
        return " ".join(normalized)
    

    def preprocess_text(self, text):
        if self.detect_short_chat(self.replace_abbreviations(text)):
            return (text, 'Tiếng Việt')

        elif self.language_check(text) == 'Tiếng Việt':
            text = self.normalize_it_terms(self.replace_abbreviations(text))
            if not self.check_tone_mark(text):
                text = self.add_tone_marks(text)
            return (text, 'Tiếng Việt')
        
        elif self.language_check(text) == 'Tiếng Anh':
            text = self.translate_to_vn(text)
            text = self.normalize_it_terms(text)
            return (text, 'Tiếng Anh')
        else:
            return (text, 'Tiếng Việt')
