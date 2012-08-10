// Copyright (c) 2006-2008 The Chromium Authors. All rights reserved.
// Use of this source code is governed by a BSD-style license that can be
// found in the LICENSE file.

#include <keyczar/base/json_writer.h>

#include <keyczar/base/logging.h>
#include <keyczar/base/stl_util-inl.h>
#include <keyczar/base/string_escape.h>
#include <keyczar/base/string_util.h>
#include <keyczar/base/values.h>

namespace {

static const char kPrettyPrintLineEnding[] = "\r\n";

}  // namespace

namespace keyczar {
namespace base {

/* static */
void JSONWriter::Write(const Value* const node, bool pretty_print,
                       std::string* json) {
  json->clear();
  // Is there a better way to estimate the size of the output?
  json->reserve(1024);
  JSONWriter writer(pretty_print, json);
  writer.BuildJSONString(node, 0);
  if (pretty_print)
    json->append(kPrettyPrintLineEnding);
}

JSONWriter::JSONWriter(bool pretty_print, std::string* json)
    : json_string_(json),
      pretty_print_(pretty_print) {
  DCHECK(json);
}

void JSONWriter::BuildJSONString(const Value* const node, int depth) {
  switch (node->GetType()) {
    case Value::TYPE_NULL:
      json_string_->append("null");
      break;

    case Value::TYPE_BOOLEAN:
      {
        bool value;
        bool result = node->GetAsBoolean(&value);
        DCHECK(result);
        json_string_->append(value ? "true" : "false");
        break;
      }

    case Value::TYPE_INTEGER:
      {
        int value;
        bool result = node->GetAsInteger(&value);
        DCHECK(result);
        json_string_->append(IntToString(value));
        break;
      }

    case Value::TYPE_REAL:
      {
        // Keyczar doesn't need float number support.
        NOTREACHED();
        break;
      }

    case Value::TYPE_STRING:
      {
        ScopedSafeString value(new std::string());
        bool result = node->GetAsString(value.get());
        DCHECK(result);
        AppendQuotedString(*value);
        break;
      }

    case Value::TYPE_LIST:
      {
        json_string_->append("[");
        if (pretty_print_)
          json_string_->append(" ");

        const ListValue* list = static_cast<const ListValue*>(node);
        for (size_t i = 0; i < list->GetSize(); ++i) {
          if (i != 0) {
            json_string_->append(",");
            if (pretty_print_)
              json_string_->append(" ");
          }

          Value* value = NULL;
          bool result = list->Get(i, &value);
          DCHECK(result);
          BuildJSONString(value, depth);
        }

        if (pretty_print_)
          json_string_->append(" ");
        json_string_->append("]");
        break;
      }

    case Value::TYPE_DICTIONARY:
      {
        json_string_->append("{");
        if (pretty_print_)
          json_string_->append(kPrettyPrintLineEnding);

        const DictionaryValue* dict =
          static_cast<const DictionaryValue*>(node);
        for (DictionaryValue::key_iterator key_itr = dict->begin_keys();
             key_itr != dict->end_keys();
             ++key_itr) {
          if (key_itr != dict->begin_keys()) {
            json_string_->append(",");
            if (pretty_print_)
              json_string_->append(kPrettyPrintLineEnding);
          }

          Value* value = NULL;
          bool result = dict->Get(*key_itr, &value);
          DCHECK(result);

          if (pretty_print_)
            IndentLine(depth + 1);
          AppendQuotedString(*key_itr);
          if (pretty_print_) {
            json_string_->append(": ");
          } else {
            json_string_->append(":");
          }
          BuildJSONString(value, depth + 1);
        }

        if (pretty_print_) {
          json_string_->append(kPrettyPrintLineEnding);
          IndentLine(depth);
          json_string_->append("}");
        } else {
          json_string_->append("}");
        }
        break;
      }

    default:
      NOTREACHED() << "unknown json type";
  }
}

void JSONWriter::AppendQuotedString(const std::string& str) {
  string_escape::JavascriptDoubleQuote(str, true, json_string_);
}

void JSONWriter::IndentLine(int depth) {
  // It may be faster to keep an indent string so we don't have to keep
  // reallocating.
  json_string_->append(std::string(depth * 3, ' '));
}

}  // namespace base
}  // namespace keyczar
