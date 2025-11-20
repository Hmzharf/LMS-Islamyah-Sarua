from django.shortcuts import render, get_object_or_404
from .models import Book
from django.db.models import Q


def catalog_view(request):
    """
    View untuk katalog buku (public)
    """
    books = Book.objects.all()
    
    # Search
    search_query = request.GET.get('search', '')
    if search_query:
        books = books.filter(
            Q(title__icontains=search_query) |
            Q(author__icontains=search_query) |
            Q(isbn__icontains=search_query)
        )
    
    # Filter by category
    category = request.GET.get('category', '')
    if category:
        books = books.filter(category=category)
    
    context = {
        'books': books,
        'search_query': search_query,
        'selected_category': category,
        'categories': Book.CATEGORY_CHOICES,
    }
    return render(request, 'books/catalog.html', context)


def book_detail_view(request, pk):
    """
    View untuk detail buku (public)
    """
    book = get_object_or_404(Book, pk=pk)
    book_copies = book.bookcopy_set.all()
    
    context = {
        'book': book,
        'book_copies': book_copies,
    }
    return render(request, 'books/detail.html', context)