from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from users.models import GuideProfile
from .models import Tour
from .forms import TourCreateForm
from django.views.generic import DetailView, ListView
from .forms import TourReviewForm
from .models import TourReview
from django.contrib.auth.decorators import login_required
from django.http import HttpResponseForbidden


class TourDetailView(DetailView):
    model = Tour
    template_name = "tours/tour_detail.html"
    context_object_name = "tour"
    slug_field = "slug"
    slug_url_kwarg = "slug"

    def get_queryset(self):
        return Tour.objects.filter(is_active=True)

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context["additional_images"] = self.object.images.all()  # galeria
        # Reviews
        context["reviews"] = self.object.reviews.select_related("tourist__user")[:10]
        context["review_form"] = TourReviewForm()
        user_review = None
        if self.request.user.is_authenticated and hasattr(
            self.request.user, "tourist_profile"
        ):
            try:
                user_review = self.object.reviews.get(
                    tourist=self.request.user.tourist_profile
                )
            except TourReview.DoesNotExist:
                user_review = None
        context["user_review"] = user_review
        return context


class TourListView(ListView):
    model = Tour
    template_name = "tours/tour_list.html"
    context_object_name = "tours"
    paginate_by = 12

    def get_queryset(self):
        return Tour.objects.filter(is_active=True).select_related("guide__user")


@login_required
def create_tour(request):
    # Kontrollo nëse përdoruesi është Guide dhe ka profil
    try:
        guide_profile = request.user.guide_profile
    except GuideProfile.DoesNotExist:
        messages.error(
            request,
            "Vetëm guidat mund të krijojnë ture. Plotëso profilin tënd së pari!",
        )
        return redirect("users:guide_profile_edit")

    if request.method == "POST":
        form = TourCreateForm(request.POST, request.FILES)
        if form.is_valid():
            tour = form.save(commit=False)
            tour.guide = guide_profile
            tour.save()
            messages.success(request, f'Turi "{tour.title}" u krijua me sukses!')
            return redirect("tours:tour_detail", slug=tour.slug)
    else:
        form = TourCreateForm()

    return render(request, "tours/create_tour.html", {"form": form})


@login_required
def create_review(request, slug):
    tour = get_object_or_404(Tour, slug=slug, is_active=True)
    # only tourists can review
    if not hasattr(request.user, "tourist_profile"):
        return HttpResponseForbidden("Only tourists can submit reviews.")

    if request.method == "POST":
        form = TourReviewForm(request.POST)
        if form.is_valid():
            rating = int(form.cleaned_data["rating"])
            comment = form.cleaned_data.get("comment", "")
            tourist = request.user.tourist_profile
            # If existing review, update it
            review, created = TourReview.objects.update_or_create(
                tour=tour,
                tourist=tourist,
                defaults={"rating": rating, "comment": comment},
            )
            messages.success(request, "Faleminderit! Vlerësimi u regjistrua.")
        else:
            messages.error(request, "Formati i vlerësimit nuk është i saktë.")
    return redirect("tours:tour_detail", slug=slug)
