import graphene


class CustomQueries(graphene.ObjectType):
    # 定义接口名称和返回类型
    hello_world = graphene.String(description="测试新增的自定义 API 接口")

    # 定义接口的处理逻辑
    def resolve_hello_world(self, info):
        # 这里可以写查询数据库、调用第三方 API 等逻辑
        return "Hello from TipTopPick Custom API!"
