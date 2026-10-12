from rest_framework import viewsets
from accounts.permissions import IsAdminLevel
from .models import Expense
from .serializers import ExpenseSerializer

class ExpenseViewSet(viewsets.ModelViewSet):
    queryset = Expense.objects.all()
    serializer_class = ExpenseSerializer
    permission_classes = [IsAdminLevel]

    def get_queryset(self):
        date = self.request.query_params.get('date')
        if date:
            return Expense.objects.filter(date=date)
        return Expense.objects.all()