import React, { useState } from 'react';
import { Search } from 'lucide-react';
import { Card, Input, Select, Textarea, Toggle, Checkbox, Rating, FileInput } from '..';

export const FormsDemo: React.FC = () => {
  const [toggle, setToggle] = useState(true);
  const [checkbox, setCheckbox] = useState(true);
  const [rating, setRating] = useState(4);

  return (
    <div className="space-y-8">
      <Card title="Text Inputs">
        <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
          <Input label="Basic Text" placeholder="Type here..." />
          <Input label="With Icon" prefix={<Search size={16} />} placeholder="Search system..." />
          <Input label="Password" type="password" placeholder="Enter secret" />
          <Input label="With Suffix" suffix=".chatty.io" placeholder="subdomain" />
          <Input label="Error State" error="This field is required" defaultValue="Invalid" />
          <Input label="Helper Text" helperText="Provide your full username." placeholder="Username" />
        </div>
      </Card>

      <Card title="Complex Inputs">
        <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
          <Select label="System Role">
            <option disabled value="">Select a role</option>
            <option value="admin">Admin</option>
            <option value="developer">Developer</option>
            <option value="user">User</option>
          </Select>
          <FileInput label="Import Configuration" variant="primary" />
          <Textarea label="Agent Description" placeholder="Define the agent's behavior..." className="md:col-span-2" />
        </div>
      </Card>

      <Card title="Selection & Toggles">
        <div className="flex flex-wrap gap-12">
          <div className="space-y-4">
            <p className="text-xs font-bold uppercase tracking-widest opacity-40">Toggles</p>
            <div className="flex flex-col gap-2">
              <Toggle label="Enable Voice Mode" checked={toggle} onChange={() => setToggle(!toggle)} color="primary" />
              <Toggle label="Debug Output" checked={toggle} onChange={() => setToggle(!toggle)} color="secondary" />
              <Toggle label="Admin Privileges" checked={toggle} onChange={() => setToggle(!toggle)} color="accent" />
            </div>
          </div>
          <div className="space-y-4">
            <p className="text-xs font-bold uppercase tracking-widest opacity-40">Checkboxes</p>
            <div className="flex flex-col gap-2">
              <Checkbox label="Remember this device" checked={checkbox} onChange={() => setCheckbox(!checkbox)} variant="primary" />
              <Checkbox label="Accept terms & conditions" checked={checkbox} onChange={() => setCheckbox(!checkbox)} variant="success" />
              <Checkbox label="Newsletter subscription" checked={checkbox} onChange={() => setCheckbox(!checkbox)} variant="info" />
            </div>
          </div>
          <div className="space-y-4">
            <p className="text-xs font-bold uppercase tracking-widest opacity-40">Rating</p>
            <div className="flex flex-col gap-4">
              <Rating value={rating} onChange={setRating} />
              <Rating value={rating} onChange={setRating} variant="warning" size="sm" />
              <Rating value={3} readOnly size="xs" />
            </div>
          </div>
        </div>
      </Card>
    </div>
  );
};
