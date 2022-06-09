def parser_messages_func(messages):
    dict_of_messages = {}
    messages = messages if not isinstance(messages, list) else list(messages)

    for each_message in messages:
        message_dict = each_message.__dict__.copy()
        del message_dict['_sa_instance_state']
        dict_of_messages[each_message.id] = message_dict

    return dict_of_messages