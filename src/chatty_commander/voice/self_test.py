# MIT License
#
# Copyright (c) 2024 mhand
#
# Permission is hereby granted, free of charge, to any person obtaining a copy
# of this software and associated documentation files (the "Software"), to deal
# in the Software without restriction, including without limitation the rights
# to use, copy, modify, merge, publish, distribute, sublicense, and/or sell
# copies of the Software, and to permit persons to whom the Software is
# furnished to do so, subject to the following conditions:
#
# The above copyright notice and this permission notice shall be included in all
# copies or substantial portions of the Software.
#
# THE SOFTWARE IS PROVIDED "AS IS", WITHOUT WARRANTY OF ANY KIND, EXPRESS OR
# IMPLIED, INCLUDING BUT NOT LIMITED TO THE WARRANTIES OF MERCHANTABILITY,
# FITNESS FOR A PARTICULAR PURPOSE AND NONINFRINGEMENT. IN NO EVENT SHALL THE
# AUTHORS OR COPYRIGHT HOLDERS BE LIABLE FOR ANY CLAIM, DAMAGES OR OTHER
# LIABILITY, WHETHER IN AN ACTION OF CONTRACT, TORT OR OTHERWISE, ARISING FROM,
# OUT OF OR IN CONNECTION WITH THE SOFTWARE OR THE USE OR OTHER DEALINGS IN THE
# SOFTWARE.

"""
Self-testing voice system using TTS→STT→LLM judge loop.

ChattyCommander can improve itself by:
1. Generate test phrases with TTS
2. Feed TTS output to STT
3. Use LLM to judge transcription accuracy
4. Automatically tune parameters and improve
"""

from __future__ import annotations

import json
import logging
import tempfile
import time

try:
    import openai
    from openai import OpenAI

    OPENAI_AVAILABLE = True
except ImportError:
    openai = None
    OpenAI = None
    OPENAI_AVAILABLE = False

try:
    import pyttsx3

    TTS_AVAILABLE = True
except ImportError:
    pyttsx3 = None
    TTS_AVAILABLE = False

from .transcription import VoiceTranscriber

logger = logging.getLogger(__name__)


class VoiceSelfTester:
    """Self-testing and improvement system for voice recognition."""

    def __init__(
        self,
        transcriber: VoiceTranscriber | None = None,
        openai_api_key: str | None = None,
        test_phrases: list[str] | None = None,
    ):
        self.transcriber = transcriber or VoiceTranscriber(backend="whisper_local")
        self.openai_client = None

        if OPENAI_AVAILABLE and openai_api_key:
            self.openai_client = OpenAI(api_key=openai_api_key)

        self.test_phrases = test_phrases or self._get_default_test_phrases()
        self._tts_engine = None

        if TTS_AVAILABLE:
            self._initialize_tts()

    def _initialize_tts(self):
        """Initialize text-to-speech engine."""
        try:
            self._tts_engine = pyttsx3.init()
            # Configure for clear speech
            self._tts_engine.setProperty("rate", 150)  # Slower for clarity
            self._tts_engine.setProperty("volume", 0.9)

            # Try to use a good quality voice
            voices = self._tts_engine.getProperty("voices")
            if voices:
                # Prefer female voices (often clearer for TTS)
                for voice in voices:
                    if (
                        "female" in voice.name.lower()
                        or "samantha" in voice.name.lower()
                    ):
                        self._tts_engine.setProperty("voice", voice.id)
                        break

        except Exception as e:
            logger.warning(f"Failed to initialize TTS: {e}")
            self._tts_engine = None

    def _get_default_test_phrases(self) -> list[str]:
        """Get default test phrases for voice recognition testing."""
        return [
            # Basic commands
            "hello world",
            "create a function",
            "open the file",
            "save and exit",
            # Programming terms
            "import numpy as np",
            "def fibonacci function",
            "async await promise",
            "class inheritance method",
            # Complex commands
            "create a Python function that validates email addresses",
            "write a recursive fibonacci function with memoization",
            "implement a binary search algorithm",
            "generate unit tests for the user authentication module",
            # Voice assistant commands
            "hey computer turn on the lights",
            "set a timer for five minutes",
            "what's the weather like today",
            "play some relaxing music",
            # Technical jargon
            "refactor the authentication middleware",
            "optimize the database query performance",
            "implement continuous integration pipeline",
            "deploy to kubernetes cluster",
        ]

    def generate_audio_from_text(self, text: str) -> bytes | None:
        """Convert text to audio using TTS."""
        if not self._tts_engine:
            logger.warning("TTS engine not available")
            return None

        try:
            with tempfile.NamedTemporaryFile(suffix=".wav", delete=False) as tmp_file:
                self._tts_engine.save_to_file(text, tmp_file.name)
                self._tts_engine.runAndWait()

                # Read the generated audio file
                with open(tmp_file.name, "rb") as f:
                    audio_data = f.read()

                return audio_data

        except Exception as e:
            logger.error(f"TTS generation failed for '{text}': {e}")
            return None

    def test_transcription_accuracy(self, text: str) -> tuple[str, float]:
        """Test transcription accuracy for a given text."""
        # Generate audio from text
        audio_data = self.generate_audio_from_text(text)
        if not audio_data:
            return "", 0.0

        # Transcribe the generated audio
        transcription = self.transcriber.transcribe_audio_data(audio_data)

        # Calculate basic accuracy (can be enhanced with LLM judge)
        accuracy = self._calculate_accuracy(text, transcription)

        return transcription, accuracy

    def _calculate_accuracy(self, original: str, transcribed: str) -> float:
        """Calculate basic word-level accuracy."""
        original_words = original.lower().split()
        transcribed_words = transcribed.lower().split()

        if not original_words:
            return 1.0 if not transcribed_words else 0.0

        # Simple word overlap calculation
        original_set = set(original_words)
        transcribed_set = set(transcribed_words)

        intersection = original_set & transcribed_set
        union = original_set | transcribed_set

        if not union:
            return 1.0

        return len(intersection) / len(union)

    def llm_judge_transcription(
        self, original: str, transcribed: str
    ) -> dict[str, any]:
        """Use LLM to judge transcription quality and provide feedback."""
        if not self.openai_client:
            return {
                "score": self._calculate_accuracy(original, transcribed),
                "feedback": "LLM judge not available",
                "suggestions": [],
            }

        prompt = f"""
        As an expert judge of speech recognition quality, evaluate this transcription:

        Original text: "{original}"
        Transcribed text: "{transcribed}"

        Please provide:
        1. A score from 0.0 to 1.0 (1.0 = perfect)
        2. Specific feedback on what went wrong (if anything)
        3. Suggestions for improvement
        4. Whether this represents a systematic error pattern

        Respond in JSON format:
        {{
            "score": 0.85,
            "feedback": "Minor issues with technical terms",
            "suggestions": ["Improve handling of programming keywords", "Add domain-specific vocabulary"],
            "error_pattern": "Technical vocabulary recognition",
            "semantic_preservation": true
        }}
        """

        try:
            response = self.openai_client.chat.completions.create(
                model="gpt-4",
                messages=[{"role": "user", "content": prompt}],
                temperature=0.1,
            )

            result = json.loads(response.choices[0].message.content)
            return result

        except Exception as e:
            logger.error(f"LLM judge failed: {e}")
            return {
                "score": self._calculate_accuracy(original, transcribed),
                "feedback": f"LLM error: {e}",
                "suggestions": [],
            }

    def run_comprehensive_test(self) -> dict[str, any]:
        """Run comprehensive self-test and return detailed results."""
        results = {
            "timestamp": time.time(),
            "total_tests": len(self.test_phrases),
            "individual_results": [],
            "summary": {
                "average_accuracy": 0.0,
                "best_category": "",
                "worst_category": "",
                "improvement_suggestions": [],
            },
        }

        logger.info(
            f"Starting comprehensive voice self-test with {len(self.test_phrases)} phrases"
        )

        category_scores = {}
        all_suggestions = []

        for i, phrase in enumerate(self.test_phrases):
            logger.info(f"Testing {i+1}/{len(self.test_phrases)}: '{phrase}'")

            # Test transcription
            transcription, basic_accuracy = self.test_transcription_accuracy(phrase)

            # LLM judge evaluation
            llm_result = self.llm_judge_transcription(phrase, transcription)

            # Categorize phrase for analysis
            category = self._categorize_phrase(phrase)
            if category not in category_scores:
                category_scores[category] = []
            category_scores[category].append(llm_result.get("score", basic_accuracy))

            # Collect suggestions
            if "suggestions" in llm_result:
                all_suggestions.extend(llm_result["suggestions"])

            test_result = {
                "phrase": phrase,
                "transcription": transcription,
                "basic_accuracy": basic_accuracy,
                "llm_score": llm_result.get("score", basic_accuracy),
                "feedback": llm_result.get("feedback", ""),
                "category": category,
                "error_pattern": llm_result.get("error_pattern", ""),
                "semantic_preservation": llm_result.get("semantic_preservation", True),
            }

            results["individual_results"].append(test_result)

        # Calculate summary statistics
        all_scores = [r["llm_score"] for r in results["individual_results"]]
        results["summary"]["average_accuracy"] = (
            sum(all_scores) / len(all_scores) if all_scores else 0.0
        )

        # Find best and worst categories
        category_averages = {
            cat: sum(scores) / len(scores) for cat, scores in category_scores.items()
        }
        if category_averages:
            results["summary"]["best_category"] = max(
                category_averages, key=category_averages.get
            )
            results["summary"]["worst_category"] = min(
                category_averages, key=category_averages.get
            )

        # Aggregate improvement suggestions
        suggestion_counts = {}
        for suggestion in all_suggestions:
            suggestion_counts[suggestion] = suggestion_counts.get(suggestion, 0) + 1

        results["summary"]["improvement_suggestions"] = [
            {"suggestion": s, "frequency": c}
            for s, c in sorted(
                suggestion_counts.items(), key=lambda x: x[1], reverse=True
            )
        ]

        logger.info(
            f"Self-test complete. Average accuracy: {results['summary']['average_accuracy']:.2%}"
        )
        return results

    def _categorize_phrase(self, phrase: str) -> str:
        """Categorize phrase for analysis."""
        phrase_lower = phrase.lower()

        if any(
            word in phrase_lower
            for word in ["function", "class", "import", "def", "async"]
        ):
            return "programming"
        elif any(
            word in phrase_lower for word in ["hey", "turn", "set", "play", "what's"]
        ):
            return "voice_commands"
        elif any(
            word in phrase_lower
            for word in ["create", "write", "implement", "generate"]
        ):
            return "creation_commands"
        elif len(phrase.split()) <= 3:
            return "simple"
        else:
            return "complex"

    def suggest_improvements(self, test_results: dict[str, any]) -> list[str]:
        """Analyze test results and suggest specific improvements."""
        suggestions = []

        summary = test_results.get("summary", {})
        avg_accuracy = summary.get("average_accuracy", 0.0)

        if avg_accuracy < 0.7:
            suggestions.append(
                "Consider switching to a higher-quality transcription backend"
            )
            suggestions.append("Improve audio preprocessing and noise reduction")

        if avg_accuracy < 0.9:
            suggestions.append("Add domain-specific vocabulary training")
            suggestions.append("Implement post-processing for common error patterns")

        # Analyze category performance
        worst_category = summary.get("worst_category")
        if worst_category:
            suggestions.append(
                f"Focus improvement efforts on '{worst_category}' category phrases"
            )

        # Extract LLM suggestions
        llm_suggestions = summary.get("improvement_suggestions", [])
        for item in llm_suggestions[:3]:  # Top 3 most frequent
            suggestions.append(f"Frequent issue: {item['suggestion']}")

        return suggestions

    def auto_tune_parameters(self, test_results: dict[str, any]) -> dict[str, any]:
        """Automatically suggest parameter adjustments based on test results."""
        tuning_recommendations = {
            "transcription_backend": "current",
            "silence_timeout": "current",
            "record_timeout": "current",
            "confidence_threshold": "current",
            "preprocessing": [],
        }

        avg_accuracy = test_results.get("summary", {}).get("average_accuracy", 0.0)

        # Suggest backend changes
        if avg_accuracy < 0.8:
            tuning_recommendations["transcription_backend"] = (
                "whisper_api"  # Higher quality
            )

        # Analyze timing issues
        individual_results = test_results.get("individual_results", [])
        timeout_issues = [
            r for r in individual_results if "timeout" in r.get("feedback", "").lower()
        ]

        if (
            len(timeout_issues) > len(individual_results) * 0.2
        ):  # More than 20% timeout issues
            tuning_recommendations["record_timeout"] = "increase"
            tuning_recommendations["silence_timeout"] = "increase"

        # Suggest preprocessing based on error patterns
        preprocessing_suggestions = []
        for result in individual_results:
            feedback = result.get("feedback", "").lower()
            if "noise" in feedback:
                preprocessing_suggestions.append("noise_reduction")
            if "volume" in feedback or "quiet" in feedback:
                preprocessing_suggestions.append("volume_normalization")
            if "speed" in feedback or "fast" in feedback:
                preprocessing_suggestions.append("speed_normalization")

        tuning_recommendations["preprocessing"] = list(set(preprocessing_suggestions))

        return tuning_recommendations


def create_self_improvement_loop(
    transcriber: VoiceTranscriber | None = None,
    openai_api_key: str | None = None,
    iterations: int = 5,
) -> dict[str, any]:
    """Create a self-improvement loop for the voice system."""

    tester = VoiceSelfTester(transcriber, openai_api_key)
    improvement_history = []

    logger.info(f"Starting self-improvement loop with {iterations} iterations")

    for iteration in range(iterations):
        logger.info(f"Self-improvement iteration {iteration + 1}/{iterations}")

        # Run comprehensive test
        results = tester.run_comprehensive_test()

        # Get improvement suggestions
        suggestions = tester.suggest_improvements(results)
        tuning = tester.auto_tune_parameters(results)

        iteration_summary = {
            "iteration": iteration + 1,
            "average_accuracy": results["summary"]["average_accuracy"],
            "best_category": results["summary"]["best_category"],
            "worst_category": results["summary"]["worst_category"],
            "suggestions": suggestions,
            "tuning_recommendations": tuning,
            "full_results": results,
        }

        improvement_history.append(iteration_summary)

        logger.info(
            f"Iteration {iteration + 1} accuracy: {results['summary']['average_accuracy']:.2%}"
        )

        # In a real implementation, we would apply the tuning recommendations here
        # For now, we just log them
        logger.info(f"Tuning recommendations: {tuning}")

        time.sleep(1)  # Brief pause between iterations

    return {
        "total_iterations": iterations,
        "improvement_history": improvement_history,
        "final_accuracy": (
            improvement_history[-1]["average_accuracy"] if improvement_history else 0.0
        ),
        "accuracy_trend": [h["average_accuracy"] for h in improvement_history],
    }


# CLI integration for self-testing
def add_self_test_commands(subparsers):
    """Add self-test commands to CLI."""

    test_parser = subparsers.add_parser(
        "self-test",
        help="Run voice system self-tests and improvements",
        description="Use TTS→STT→LLM judge loop to test and improve voice recognition",
    )

    test_subparsers = test_parser.add_subparsers(
        dest="test_command", help="Self-test commands"
    )

    # Basic test
    basic_parser = test_subparsers.add_parser("run", help="Run basic self-test")
    basic_parser.add_argument("--openai-key", help="OpenAI API key for LLM judge")
    basic_parser.add_argument("--phrases", nargs="+", help="Custom test phrases")

    # Improvement loop
    improve_parser = test_subparsers.add_parser(
        "improve", help="Run self-improvement loop"
    )
    improve_parser.add_argument(
        "--iterations", type=int, default=3, help="Number of improvement iterations"
    )
    improve_parser.add_argument("--openai-key", help="OpenAI API key for LLM judge")

    # Benchmark
    benchmark_parser = test_subparsers.add_parser(
        "benchmark", help="Run comprehensive benchmark"
    )
    benchmark_parser.add_argument("--openai-key", help="OpenAI API key for LLM judge")
    benchmark_parser.add_argument(
        "--save-results", help="File to save detailed results"
    )


def handle_self_test_command(args):
    """Handle self-test CLI commands."""

    if not hasattr(args, "test_command") or not args.test_command:
        print("No self-test command specified. Use --help for available commands.")
        return

    # Check dependencies
    if not TTS_AVAILABLE:
        print("❌ TTS not available. Install with: pip install pyttsx3")
        return

    if args.test_command == "run":
        print("🧪 Running voice self-test...")

        tester = VoiceSelfTester(
            openai_api_key=getattr(args, "openai_key", None),
            test_phrases=getattr(args, "phrases", None),
        )

        results = tester.run_comprehensive_test()

        print("📊 Test Results:")
        print(f"   Average accuracy: {results['summary']['average_accuracy']:.2%}")
        print(f"   Best category: {results['summary']['best_category']}")
        print(f"   Worst category: {results['summary']['worst_category']}")

        suggestions = tester.suggest_improvements(results)
        if suggestions:
            print("\n💡 Improvement suggestions:")
            for suggestion in suggestions[:5]:  # Top 5
                print(f"   • {suggestion}")

    elif args.test_command == "improve":
        print("🔄 Running self-improvement loop...")

        transcriber = VoiceTranscriber(backend="whisper_local")

        results = create_self_improvement_loop(
            transcriber=transcriber,
            openai_api_key=getattr(args, "openai_key", None),
            iterations=getattr(args, "iterations", 3),
        )

        print("📈 Improvement Results:")
        print(f"   Final accuracy: {results['final_accuracy']:.2%}")
        print(f"   Accuracy trend: {[f'{a:.1%}' for a in results['accuracy_trend']]}")

    elif args.test_command == "benchmark":
        print("📏 Running comprehensive benchmark...")

        tester = VoiceSelfTester(openai_api_key=getattr(args, "openai_key", None))
        results = tester.run_comprehensive_test()

        if hasattr(args, "save_results") and args.save_results:
            with open(args.save_results, "w") as f:
                json.dump(results, f, indent=2)
            print(f"💾 Detailed results saved to {args.save_results}")

        print(
            f"🏆 Benchmark complete: {results['summary']['average_accuracy']:.2%} accuracy"
        )
