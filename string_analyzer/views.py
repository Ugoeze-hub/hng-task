# from django.shortcuts import render
from pydoc import text
from django.http import HttpResponse
from rest_framework.decorators import api_view
from rest_framework.response import Response
from rest_framework import status
from .models import AnalyzedString
from .serializer import AnalyzedStringSerializer
import hashlib
from collections import Counter
import re

@api_view(['GET'])
def home(request):
    values = AnalyzedString.objects.all()
    serializer = AnalyzedStringSerializer(values, many=True)
    return Response(serializer.data)


@api_view(['POST'])
def strings(request):
    value = request.data.get('value', '')
    if not value:
        return Response({"error": "Invalid request body or missing 'value' field"}, status=status.HTTP_400_BAD_REQUEST)
    elif not isinstance(value, str):
        return Response({"error": "Invalid data type for 'value' (must be string)"}, status=status.HTTP_422_UNPROCESSABLE_ENTITY)
    
    sha256_hash = hashlib.sha256(value.encode()).hexdigest()

    if AnalyzedString.objects.filter(sha256_hash=sha256_hash).exists():
        return Response({"error": "String has already been analyzed"}, status=status.HTTP_409_CONFLICT)
    
    #doing the analysis
    length = len(value)
    is_palindrome = value.lower() == value.lower()[::-1]
    unique_characters = len(set(value))
    word_count = len(value.split())
    character_frequency_map = dict(Counter(value))

    #putting it back in my db
    analyzed_value = AnalyzedString.objects.create(
        value=value,
        length=length,
        is_palindrome=is_palindrome,
        unique_characters=unique_characters,
        word_count=word_count,
        sha256_hash=sha256_hash,
        character_frequency_map=character_frequency_map
    )
    try:
        serializer = AnalyzedStringSerializer(analyzed_value)
        return Response({
            "id": sha256_hash, 
            "value": value,
            "properties": {
                "length": length,
                "is_palindrome": is_palindrome,
                "unique_characters": unique_characters,
                "word_count": word_count,
                "sha256_hash": sha256_hash,
                "character_frequency_map": character_frequency_map
            },
            "created_at": analyzed_value.created_at
        }, status=status.HTTP_201_CREATED)
    except Exception as e:
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

@api_view(['GET'])
def get_string(request, specific_string):
    try:
        specific_analyzed_string = AnalyzedString.objects.get(value=specific_string)
        try:
            serializer = AnalyzedStringSerializer(specific_analyzed_string)
            return Response({
                "id": specific_analyzed_string.sha256_hash,
                "value": specific_analyzed_string.value,
                "properties": {
                    "length": specific_analyzed_string.length,
                    "is_palindrome": specific_analyzed_string.is_palindrome,
                    "unique_characters": specific_analyzed_string.unique_characters,
                    "word_count": specific_analyzed_string.word_count,
                    "sha256_hash": specific_analyzed_string.sha256_hash,
                    "character_frequency_map": specific_analyzed_string.character_frequency_map
                },
                "created_at": specific_analyzed_string.created_at
            }, status=status.HTTP_200_OK)
        except Exception as e:
            return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)
    except AnalyzedString.DoesNotExist:
        return Response({"error": "String does not exist in the system"}, status=status.HTTP_404_NOT_FOUND)


@api_view(['GET'])
def get_filtered_strings(request):
    try:
        all_strings = AnalyzedString.objects.all()

        is_palindrome = request.query_params.get('is_palindrome', None)
        min_length = request.query_params.get('min_length', None)   
        max_length = request.query_params.get('max_length', None)
        word_count = request.query_params.get('word_count', None)
        contains_character = request.query_params.get('contains_character', None)

        applied_filters = {}

        if is_palindrome is not None:
            if is_palindrome.lower() not in ['true', 'false']:
                return Response({"error": "Invalid query parameter values or types"}, status=status.HTTP_400_BAD_REQUEST)
            is_palindrome_bool = is_palindrome.lower() == 'true'
            all_strings = all_strings.filter(is_palindrome=is_palindrome_bool)
            applied_filters['is_palindrome'] = is_palindrome_bool

        if min_length is not None:
            if not min_length.isdigit():
                return Response({"error": "Invalid query parameter values or types"}, status=status.HTTP_400_BAD_REQUEST)
            all_strings = all_strings.filter(length__gte=int(min_length))
            applied_filters['min_length'] = int(min_length)

        if max_length is not None:
            if not max_length.isdigit():
                return Response({"error": "Invalid query parameter values or types"}, status=status.HTTP_400_BAD_REQUEST)
            all_strings = all_strings.filter(length__lte=int(max_length))
            applied_filters['max_length'] = int(max_length)

        if word_count is not None:
            if not word_count.isdigit():
                return Response({"error": "Invalid query parameter values or types"}, status=status.HTTP_400_BAD_REQUEST)
            all_strings = all_strings.filter(word_count=int(word_count))
            applied_filters['word_count'] = int(word_count)

        if contains_character is not None:
            if len(contains_character) != 1:
                return Response({"error": "Invalid query parameter values or types"}, status=status.HTTP_400_BAD_REQUEST)
            all_strings = all_strings.filter(value__icontains=contains_character)
            applied_filters['contains_character'] = contains_character

        data = []
        for string in all_strings:
            data.append({
                "id": string.sha256_hash,
                "value": string.value,
                "properties": {
                    "length": string.length,
                    "is_palindrome": string.is_palindrome,
                    "unique_characters": string.unique_characters,
                    "word_count": string.word_count,
                    "sha256_hash": string.sha256_hash,
                    "character_frequency_map": string.character_frequency_map
                },
                "created_at": string.created_at
            })
        return Response({
            "data": data,
            "count": len(data),
            "filters_applied": applied_filters
        }, status=status.HTTP_200_OK)
    
    except Exception as e:
        return Response({"error": str(e)}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)



    
@api_view(['GET'])
def natural_language_filter(request):
    try:
        query = request.query_params.get('query', None).lower().strip()
        if not query:
            return Response({"error": "Unable to parse natural language query"}, status=status.HTTP_400_BAD_REQUEST) 

        natural_language_filters = {}

        if "palindrome" or "palindromic" in query:
            natural_language_filters['is_palindrome'] = True

        if "single word" in query:
            natural_language_filters['word_count'] = 1
        elif "multiple words" in query:
            natural_language_filters['word_count__gt'] = 1

        contains_letter = re.search(r"(?:containing|have|with|including) the letter ([a-z])", query)
        if contains_letter:
            natural_language_filters['value__icontains'] = contains_letter.group(1)
            
        contains_vowel = re.search(r"(?:contain|include|have|feature).*vowel\s*([aeiou])?", query)
        if contains_vowel:
            vowel = contains_vowel.group(1) if contains_vowel.group(1) else "a"
            natural_language_filters["value__icontains"] = vowel

        if not natural_language_filters:
            return Response({"error": "Unable to parse natural language query"}, status=status.HTTP_400_BAD_REQUEST)
        
        filtered_strings = AnalyzedString.objects.filter(**natural_language_filters)

        data = []
        for string in filtered_strings:
            data.append({
                "id": string.sha256_hash,
                "value": string.value,
                "properties": {
                    "length": string.length,
                    "is_palindrome": string.is_palindrome,
                    "unique_characters": string.unique_characters,
                    "word_count": string.word_count,
                    "sha256_hash": string.sha256_hash,
                    "character_frequency_map": string.character_frequency_map
                },
                "created_at": string.created_at
            })

        if not data:
            return Response({"error": "Query parsed but resulted in no matches."}, status=status.HTTP_422_UNPROCESSABLE_ENTITY)
        
        return Response({
            "data": data,
            "count": len(data),
            "interpreted_query": {
                "original": query,
                "parsed_filters": natural_language_filters
            }
        }, status=status.HTTP_200_OK)
    
    except Exception as e:
        return Response({"error": str(e)}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)   



@api_view(['DELETE'])
def delete_string(request, specific_string):
    try:
        specific_analyzed_string = AnalyzedString.objects.get(value=specific_string)
        specific_analyzed_string.delete()
        return Response({"message": "String successfully deleted"}, status=status.HTTP_200_OK)
    except AnalyzedString.DoesNotExist:
        return Response({"error": "String does not exist in the system"}, status=status.HTTP_404_NOT_FOUND)
    except Exception as e:
        return Response(
            {"error": f"An unexpected error occurred: {str(e)}"},
            status=status.HTTP_500_INTERNAL_SERVER_ERROR
        )