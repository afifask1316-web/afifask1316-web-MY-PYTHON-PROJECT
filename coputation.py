time=float(input("enter daily hours your:"))
overtime=float(input("enter your over time:"))
regularpay=time*100
amount=regularpay+15*overtime
print("the your regular day amount is :",regularpay)
print("the your over time with daily worked amount is :",amount)
your=regularpay*30
year=amount*365//9
print("your yearly salary with extra working is :",year)
print("your monthly salary is :",your)